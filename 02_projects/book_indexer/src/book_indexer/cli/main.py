import json
import math
import sqlite3
import sys
import time
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen
import book_indexer
print(book_indexer.__file__)


from book_indexer.scan.filesystem import scan_directory
from book_indexer.core.builder import build_book
from book_indexer.storage.sqlite import cleanup_missing_books
from book_indexer.storage.sqlite import get_book_file_info
from book_indexer.storage.sqlite import init_db
from book_indexer.storage.sqlite import mark_seen_bulk
from book_indexer.storage.sqlite import save_index_sqlite
from book_indexer.storage.search import search_books

DB_PATH = "index.db"
STOPWORDS = {"что", "такое", "это", "как", "когда", "почему", "где"}


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding(text):
    payload = json.dumps(
        {
            "model": "nomic-embed-text",
            "prompt": text[:1000],
        }
    ).encode("utf-8")

    request = Request(
        "http://localhost:11434/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except (OSError, URLError, TimeoutError, ValueError):
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None

    return data.get("embedding")


def normalize_query(query: str) -> str:
    q = query.lower()

    for prefix in ["что такое", "что это", "кто такой", "что значит"]:
        if q.startswith(prefix):
            q = q[len(prefix):].strip()

    return q


def index(path: str):
    init_db(DB_PATH)
    current_run = time.time()

    files = scan_directory(path)

    books_with_status = []
    paths = []
    unchanged = 0

    for f in files:
        paths.append(str(f))

        existing_meta = get_book_file_info(f, DB_PATH)
        book, status = build_book(f, existing_meta)

        if status == "unchanged":
            unchanged += 1

        if book:
            books_with_status.append((book, status))

    save_stats = save_index_sqlite(books_with_status, DB_PATH, path, current_run)

    mark_seen_bulk(paths, DB_PATH, current_run)

    removed = cleanup_missing_books(DB_PATH, path, current_run)

    print(f"+{save_stats['added']} added")
    print(f"~{save_stats['updated']} updated")
    print(f"-{removed} removed")
    print(f"={unchanged} unchanged")


def search(text: str, display: bool = True):
    init_db(DB_PATH)
    rows = search_books(DB_PATH, text)

    if not rows:
        if display:
            print("No results found")
        return []

    rows = sorted(rows, key=lambda x: (x[1] or "").lower())
    rows = rows[:20]

    if not display:
        return rows

    print(f"Found {len(rows)} results\n")

    for i, (path, title, author, _description) in enumerate(rows, 1):
        title = title or "[no title]"
        author = author or "[no author]"
        author = " ".join(author.split()) if author else author

        print(f"{i}. {title} — {author}")
        print(f"   {path}")
        print()

    return rows


def show(text: str):
    rows = search(text, display=False)
    if not rows:
        print("No results found")
        return

    path, title, author, description = rows[0]
    title = title or "[no title]"
    author = author or "[no author]"
    description = description or "[no description]"

    print(f"{title} — {author}")
    print(f"Description: {description}")
    print(f"Path: {path}")


def _get_semantic_top(text: str):
    query_norm = normalize_query(text)
    query_emb = get_embedding(query_norm)
    if not query_emb:
        return []

    query_lower = text.lower()

    init_db(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT book_path, text, embedding FROM book_chunks WHERE embedding IS NOT NULL"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    results = []

    for path, chunk_text, emb_json in rows:
        if not chunk_text or len(chunk_text) < 300:
            continue  # фильтр мусора

        try:
            emb = json.loads(emb_json)
        except (TypeError, json.JSONDecodeError):
            continue

        score = cosine_similarity(query_emb, emb)
        text_lower = chunk_text.lower()

        explain_boost = 0.0

        if "— это" in text_lower:
            explain_boost += 0.08
        elif " это " in text_lower:
            explain_boost += 0.05

        if "является" in text_lower:
            explain_boost += 0.05

        if "представляет собой" in text_lower:
            explain_boost += 0.05

        score += explain_boost

        # --- аккуратный keyword boost ---
        boost = 0.0

        for word in query_lower.split():
            if word in STOPWORDS:
                continue

            if len(word) < 5:
                continue

            root = word[:8]

            if root in text_lower:
                boost += 0.03

            if word in text_lower:
                boost += 0.05

        score += min(boost, 0.15)

        results.append((score, path, chunk_text))

    if not results:
        return []

    results.sort(reverse=True)
    return results[:10]


def semantic_search(text: str):
    top = _get_semantic_top(text)
    if not top:
        print("No results found")
        return

    for score, path, chunk_text in top:
        print(f"\n[{score:.3f}] {path}")
        print((chunk_text or "")[:300])


def ask_llm(question: str, context: str) -> str:
    prompt = f"""
Ответь на вопрос, используя только контекст ниже.
Ответь на вопрос кратко и по существу.
Если в контексте есть определение — используй его.

Не придумывай информацию.
Если ответа нет — скажи, что не найдено.

Контекст:
{context}

Вопрос:
{question}

Ответ:
"""

    data = json.dumps(
        {
            "model": "mistral",
            "prompt": prompt,
            "stream": False,
        }
    ).encode("utf-8")

    req = Request(
        "http://localhost:11434/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
        return ""

    return result.get("response", "")


def semantic_search_and_answer(text: str):
    top = _get_semantic_top(text)
    if not top:
        print("No results found")
        return

    context = "\n\n".join(chunk_text for _, _, chunk_text in top)
    answer = ask_llm(text, context)

    print("\n=== ANSWER ===\n")
    print(answer)
    print("\n=== SOURCES ===\n")
    for score, path, _ in top:
        print(f"{path} [{score:.3f}]")


def main():
    print("cli started")

    if len(sys.argv) < 2:
        print("commands: index | search | show | ask | ask2")
        return

    cmd = sys.argv[1]

    if cmd == "index":
        if len(sys.argv) < 3:
            print("need path")
            return

        index(sys.argv[2])
    elif cmd == "search":
        search(sys.argv[2])
    elif cmd == "show":
        if len(sys.argv) < 3:
            print("need query")
            return

        show(sys.argv[2])
    elif cmd == "ask":
        if len(sys.argv) < 3:
            print("need query")
            return

        semantic_search(" ".join(sys.argv[2:]))
    elif cmd == "ask2":
        if len(sys.argv) < 3:
            print("need query")
            return

        semantic_search_and_answer(" ".join(sys.argv[2:]))


if __name__ == "__main__":
    main()
