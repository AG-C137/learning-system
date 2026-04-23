"""
Service layer for book_indexer business logic.
Provides pure functions without CLI/printing side effects.
"""
import json
import math
import re
import sqlite3
from urllib.error import URLError
from urllib.request import Request, urlopen

from book_indexer.storage.sqlite import init_db, load_book_metadata
from book_indexer.storage.search import search_books

DB_PATH = "index.db"
MAX_CONTEXT_CHUNKS = 4
MIN_CONTEXT_SCORE = 0.7
MIN_DEFINITION_SCORE = 0.8
MIN_ANSWER_SCORE = 0.75
STOPWORDS = {"что", "такое", "это", "как", "когда", "почему", "где"}


def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def get_embedding(text):
    """Get embedding from ollama API."""
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
    """Normalize and clean query text."""
    q = query.lower()

    for prefix in ["что такое", "что это", "кто такой", "что значит"]:
        if q.startswith(prefix):
            q = q[len(prefix) :].strip()

    return q


def is_definition(text: str) -> bool:
    """Check if text is a definition."""
    if not text:
        return False

    snippet = text.strip()[:300]
    sentence = re.split(r"[.!?]", snippet)[0].strip()
    pattern = r"^[А-ЯA-Z][^.!?]{0,100}\s[—-]\sэто\s"

    if re.search(pattern, sentence, re.IGNORECASE):
        return True

    return False


def has_keyword(text: str, query: str) -> bool:
    """Check if text contains query keywords."""
    if not text or not query:
        return False

    text_lower = text.lower()
    for word in query.lower().split():
        if word and word in text_lower:
            return True

    return False


def load_chunks():
    """Load all chunks from database with embeddings."""
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

    books_map = load_book_metadata(DB_PATH)
    chunks = []

    for path, chunk_text, emb_json in rows:
        if not chunk_text or len(chunk_text) < 300:
            continue

        try:
            emb = json.loads(emb_json)
        except (TypeError, json.JSONDecodeError):
            continue

        chunk = {
            "source": path,
            "book_path": path,
            "text": chunk_text,
            "embedding": emb,
        }

        meta = books_map.get(path)
        if meta:
            chunk["title"] = meta.get("title")
            chunk["author"] = meta.get("author")

        chunks.append(chunk)

    return chunks


def load_and_filter_chunks(book: str | None = None, author: str | None = None) -> list[dict]:
    """Load chunks and filter by book/author."""
    all_chunks = load_chunks()

    if book:
        book_lower = book.lower()
        all_chunks = [
            chunk
            for chunk in all_chunks
            if book_lower in (chunk.get("title") or "").lower()
        ]

    if author:
        author_lower = author.lower()
        all_chunks = [
            chunk
            for chunk in all_chunks
            if author_lower in (chunk.get("author") or "").lower()
        ]

    return all_chunks


def semantic_rank(chunks: list[dict], text: str) -> list[dict]:
    """Rank chunks by semantic similarity."""
    query_norm = normalize_query(text)
    query_emb = get_embedding(query_norm)
    if not query_emb:
        return []

    query_lower = text.lower()
    title_query = query_norm.lower()
    results = []

    for chunk in chunks:
        path = chunk["book_path"]
        chunk_text = chunk["text"]
        emb = chunk["embedding"]
        score = cosine_similarity(query_emb, emb)
        text_lower = chunk_text.lower()

        explain_boost = 0.0

        if is_definition(chunk_text):
            explain_boost += 0.08

        score += explain_boost

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
                "source": path,
                "book_path": path,
                "text": chunk_text,
            }
        )

    if not results:
        return []

    results.sort(key=lambda item: item["score"], reverse=True)

    return results


def _generate_with_llm(prompt: str) -> str:
    """Generate text using ollama API."""
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
    """Ask LLM with optional context."""
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
Ты — ассистент, отвечающий на основе содержания книг.

Контекст из книги:
{context}

Вопрос:
{question}

Если в контексте есть определение (формат "X — это ..."):
— ОБЯЗАТЕЛЬНО используй его как основу ответа.

Если есть несколько вариантов — выбери самый общий.

Если нет информации — скажи "нет информации".

Ответ:
"""

    return _generate_with_llm(prompt)


def rerank_chunks(question: str, chunks: list[dict]) -> list[int]:
    """Rerank chunks using LLM."""
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


def rank_chunks(chunks: list[dict], query: str) -> tuple[list[dict], float]:
    """Rank chunks and return with max score."""
    chunks = semantic_rank(chunks, query)
    keyword_chunks = [c for c in chunks if has_keyword(c["text"], query)]
    if keyword_chunks:
        for c in keyword_chunks:
            c["score"] += 0.3

    chunks = chunks[:50]

    chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
    max_score = chunks[0]["score"] if chunks else 0.0

    return chunks, max_score


def rerank_and_select(chunks: list[dict], query: str) -> list[dict]:
    """Rerank and select top chunks for context."""
    if len(chunks) > 20:
        chunks = chunks[:20]

    indices = rerank_chunks(query, chunks)

    if indices and len(indices) >= 3:
        selected_chunks = [chunks[i] for i in indices]
    else:
        selected_chunks = chunks

    selected_chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
    context_chunks = selected_chunks[:MAX_CONTEXT_CHUNKS]

    return context_chunks


def filter_definitions(definition_chunks, query):
    """Filter definitions by relevance."""
    result = []

    query_words = query.lower().split()

    for c in definition_chunks:
        text_lower = c["text"].lower()

        keyword_ok = any(w in text_lower for w in query_words)
        score_ok = c["score"] >= 0.8

        if keyword_ok and score_ok:
            result.append(c)

    return result


def process_context(context_chunks: list[dict], query: str) -> tuple[list[dict], list[dict]]:
    """Process context chunks, prioritize definitions."""
    definition_chunks = [
        c for c in context_chunks if is_definition(c["text"])
    ]

    definition_chunks = filter_definitions(definition_chunks, query)

    if definition_chunks:
        context_chunks = definition_chunks + context_chunks

        seen = set()
        unique = []
        for c in context_chunks:
            key = c["text"][:100]
            if key not in seen:
                seen.add(key)
                unique.append(c)

        context_chunks = unique[:MAX_CONTEXT_CHUNKS]

    return context_chunks, definition_chunks


def _format_sources(chunks: list[dict]) -> list[dict]:
    """Format chunks as sources for response."""
    seen_books = {}
    for chunk in chunks:
        book_path = chunk["book_path"]
        if book_path not in seen_books:
            meta = load_book_metadata(DB_PATH).get(book_path, {})
            seen_books[book_path] = {
                "path": book_path,
                "score": chunk["score"],
                "title": chunk.get("title") or meta.get("title") or "[no title]",
                "author": chunk.get("author") or meta.get("author") or "[no author]",
            }

    return list(seen_books.values())


def ask(
    query: str, book: str | None = None, author: str | None = None, debug: bool = False
) -> dict:
    """
    Main API function: ask a question and get answer with sources.
    
    Args:
        query: Question text
        book: Filter by book title (optional)
        author: Filter by author name (optional)
        debug: Include debug info in response
    
    Returns:
        {
            "answer": str,
            "sources": list[dict],  # [{path, score, title, author}, ...]
            "confidence": float,
            "debug": dict  # optional, if debug=True
        }
    """
    debug_info = {} if debug else None

    def build_response(answer: str, sources: list[dict], confidence: float) -> dict:
        response = {
            "answer": answer,
            "sources": sources,
            "confidence": confidence,
        }
        if debug_info is not None:
            response["debug"] = debug_info
        return response

    # Load and filter chunks
    all_chunks = load_and_filter_chunks(book=book, author=author)

    if debug_info is not None:
        debug_info["chunks_loaded"] = len(all_chunks)

    # No chunks available
    if not all_chunks:
        if debug_info is not None:
            debug_info["status"] = "empty_db"
        return build_response("в базе нет информации", [], 0.0)

    # Rank chunks
    chunks, max_score = rank_chunks(all_chunks, query)

    if debug_info is not None:
        debug_info["chunks_ranked"] = len(chunks)
        debug_info["max_score"] = max_score

    # Threshold check
    THRESHOLD = 0.7
    if max_score < THRESHOLD:
        if debug_info is not None:
            debug_info["status"] = "low_threshold"
            debug_info["threshold"] = THRESHOLD

        return build_response("Недостаточно релевантной информации в базе...", [], max_score)

    # Rerank and select context
    context_chunks = rerank_and_select(chunks, query)
    context_chunks, definition_chunks = process_context(context_chunks, query)

    if debug_info is not None:
        debug_info["context_chunks"] = len(context_chunks)
        debug_info["definition_chunks"] = len(definition_chunks)

    # Check for definition shortcut
    if definition_chunks and max_score > 0.8:
        best = sorted(definition_chunks, key=lambda c: c["score"], reverse=True)[0]

        if best["score"] >= MIN_DEFINITION_SCORE:
            if debug_info is not None:
                debug_info["status"] = "definition_found"

            sources = _format_sources([best])
            return build_response(best["text"].strip(), sources, max_score)

    # Guard: reject if context is weak
    if not context_chunks or max_score < MIN_ANSWER_SCORE:
        if debug_info is not None:
            debug_info["status"] = "weak_context"
            debug_info["max_score"] = max_score

        return build_response("Недостаточно релевантной информации в базе...", [], max_score)

    # Check minimum context score
    best_score = context_chunks[0]["score"] if context_chunks else 0.0
    if best_score < MIN_CONTEXT_SCORE:
        if debug_info is not None:
            debug_info["status"] = "low_context_score"
            debug_info["best_score"] = best_score

        return build_response("Недостаточно релевантной информации в базе...", [], max_score)

    # Generate answer with context
    if debug_info is not None:
        debug_info["status"] = "answer_from_context"

    context = "\n\n".join(chunk["text"] for chunk in context_chunks)
    answer = ask_llm(query, context)

    sources = _format_sources(context_chunks)

    return build_response(answer, sources, max_score)


def search(query: str) -> list[dict]:
    """
    Search for books by text.
    
    Returns:
        list[dict]  # [{path, title, author, description}, ...]
    """
    init_db(DB_PATH)
    rows = search_books(DB_PATH, query)

    if not rows:
        return []

    rows = sorted(rows, key=lambda x: (x[1] or "").lower())
    rows = rows[:20]

    results = []
    for path, title, author, description in rows:
        results.append(
            {
                "path": path,
                "title": title or "[no title]",
                "author": author or "[no author]",
                "description": description or "[no description]",
            }
        )

    return results


def list_books() -> list[dict]:
    """
    List all books in database.
    
    Returns:
        list[dict]  # [{path, title, author}, ...]
    """
    init_db(DB_PATH)
    books_map = load_book_metadata(DB_PATH)

    results = []
    for path, meta in books_map.items():
        results.append(
            {
                "path": path,
                "title": meta.get("title") or "[no title]",
                "author": meta.get("author") or "[no author]",
            }
        )

    return results
