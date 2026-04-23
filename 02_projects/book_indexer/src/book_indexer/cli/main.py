import json
import re
import sqlite3
import sys
import time

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

from book_indexer.api.service import ask, semantic_rank, load_chunks

DB_PATH = "index.db"


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
    all_chunks = load_chunks()
    ranked_chunks = semantic_rank(all_chunks, text)

    return [
        (item["score"], item["book_path"], item["text"])
        for item in ranked_chunks[:10]
    ]


def semantic_search(text: str):
    top = _get_semantic_top(text)
    if not top:
        print("No results found")
        return

    for score, path, chunk_text in top:
        print(f"\n[{score:.3f}] {path}")
        print((chunk_text or "")[:300])


def semantic_search_and_answer(query: str, book: str | None = None, author: str | None = None):
    """Wrapper over service.ask() with CLI output formatting."""
    if book:
        print(f"[mode] book={book}")
    elif author:
        print(f"[mode] author={author}")
    else:
        print("[mode] all")

    # Call service layer
    result = ask(query, book=book, author=author, debug=True)

    # Extract debug info
    debug_info = result.get("debug", {})

    if debug_info:
        print(f"[debug] chunks_found={debug_info.get('chunks_ranked', 0)}")
        print(f"[debug] max_score={debug_info.get('max_score', 0.0):.3f}")
        print(f"[debug] context_chunks={debug_info.get('context_chunks', 0)}")
        print(f"[debug] definition_chunks={debug_info.get('definition_chunks', 0)}")

    # Print answer
    print("\n=== ANSWER ===\n")
    print(result.get("answer", ""))

    # Print sources
    sources = result.get("sources", [])
    if sources:
        print("\n=== SOURCES ===\n")
        for source in sources:
            print(f"{source['path']} [{source['score']:.3f}]")


def _parse_ask2_args(args: list[str]) -> tuple[str | None, str | None, str | None]:
    book = None
    author = None
    query_parts = []
    i = 0

    while i < len(args):
        arg = args[i]

        if arg == "--book":
            if i + 1 >= len(args):
                return None, None, None
            book = args[i + 1]
            i += 2
            continue

        if arg == "--author":
            if i + 1 >= len(args):
                return None, None, None
            author = args[i + 1]
            i += 2
            continue

        query_parts.append(arg)
        i += 1

    query = " ".join(query_parts).strip()
    return query or None, book, author


def main():
    print("cli started")

    if len(sys.argv) < 2:
        print("commands: index | search | show | ask | ask2 [--book NAME] [--author NAME] <query>")
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
        query, book, author = _parse_ask2_args(sys.argv[2:])
        if not query:
            print("need query")
            return

        semantic_search_and_answer(query, book=book, author=author)


if __name__ == "__main__":
    main()
