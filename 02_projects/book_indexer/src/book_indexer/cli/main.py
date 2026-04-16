import json
import math
import re
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
MAX_CONTEXT_CHUNKS = 4
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


def looks_like_definition(text: str) -> bool:
    if not text:
        return False

    t = text[:300].lower()

    patterns = [
        r"^[^\.]{0,80}\s—\sэто\s",
        r"^[^\.]{0,80}\sэто\s",
        r"^[^\.]{0,80}\sявляется\s",
        r"^[^\.]{0,80}\sпредставляет собой\s",
    ]

    for pattern in patterns:
        if re.search(pattern, t):
            return True

    return False


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
    title_query = query_norm.lower()

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

        if title_query and title_query in path.lower():
            score += 0.2

        results.append(
            {
                "score": score,
                "book_path": path,
                "text": chunk_text,
            }
        )

    if not results:
        return []

    results.sort(key=lambda item: item["score"], reverse=True)

    seen_books = set()
    unique_results = []

    for item in results:
        book_path = item["book_path"]

        if book_path in seen_books:
            continue

        seen_books.add(book_path)
        unique_results.append(item)

    results = unique_results

    return [
        (item["score"], item["book_path"], item["text"])
        for item in results[:10]
    ]


def semantic_search(text: str):
    top = _get_semantic_top(text)
    if not top:
        print("No results found")
        return

    for score, path, chunk_text in top:
        print(f"\n[{score:.3f}] {path}")
        print((chunk_text or "")[:300])


def _generate_with_llm(prompt: str) -> str:
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


def ask_llm(question: str, context: str | None = None) -> str:
    if context is None:
        prompt = f"""
Ответь на вопрос кратко и по существу.
Если ты не уверен, так и скажи.

Вопрос:
{question}

Ответ:
"""
        return _generate_with_llm(prompt)

    prompt = f"""
Ты — ассистент, отвечающий на основе книг.

Контекст из книги:
{context}

Вопрос:
{question}

Ответь ТОЛЬКО на основе контекста.
Если в контексте нет ответа — скажи: "в базе нет информации".
Не придумывай информацию и не добавляй знания вне контекста.

Ответ:
"""

    return _generate_with_llm(prompt)


def rerank_chunks(question: str, chunks: list[dict]) -> list[int]:
    if not chunks:
        return []

    prompt_parts = []

    for i, chunk in enumerate(chunks, 1):
        text = (chunk.get("text") or "")[:500]
        prompt_parts.append(f"[{i}]\n{text}")

    prompt = f"""
Вопрос:
{question}

Ниже фрагменты текста. Выбери номера фрагментов, которые прямо помогают ответить на вопрос.

Игнорируй художественные тексты, общие рассуждения и нерелевантные куски.

Ответ верни ТОЛЬКО в формате:
[1, 3, 5]

Если ничего не подходит — верни [].

Фрагменты:

{'\n\n'.join(prompt_parts)}
"""

    response = _generate_with_llm(prompt)
    numbers = re.findall(r"\d+", response)

    indices = []
    for number in numbers:
        index = int(number) - 1
        if 0 <= index < len(chunks) and index not in indices:
            indices.append(index)

    return indices


def semantic_search_and_answer(text: str):
    top = _get_semantic_top(text)
    if not top:
        print("\n=== ANSWER ===\n")
        print("Не найдено в базе. Генерирую общий ответ...\n")
        print(ask_llm(text))
        return

    chunks = [
        {"score": score, "book_path": path, "text": chunk_text}
        for score, path, chunk_text in top
    ]
    chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
    max_score = chunks[0]["score"] if chunks else 0.0

    indices = rerank_chunks(text, chunks)

    if indices:
        selected_chunks = [chunks[i] for i in indices]
        selected_chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
        context_chunks = selected_chunks[:MAX_CONTEXT_CHUNKS]
    else:
        context_chunks = chunks[:MAX_CONTEXT_CHUNKS]

    has_definition = any(
        looks_like_definition(chunk["text"])
        for chunk in context_chunks
    )

    print(f"[debug] chunks_found={len(chunks)}")
    print(f"[debug] max_score={max_score:.3f}")
    print(f"[debug] has_definition={has_definition}")

    if not context_chunks:
        print("\n=== ANSWER ===\n")
        print("Нет надёжной информации в базе. Генерирую общий ответ...\n")
        print(ask_llm(text))
        return

    context = "\n\n".join(chunk["text"] for chunk in context_chunks)
    answer = ask_llm(text, context)

    print("\n=== ANSWER ===\n")
    print(answer)
    print("\n=== SOURCES ===\n")
    for chunk in context_chunks:
        print(f"{chunk['book_path']} [{chunk['score']:.3f}]")


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
