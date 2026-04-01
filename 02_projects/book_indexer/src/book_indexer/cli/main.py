import sys
import time

from book_indexer.scan.filesystem import scan_directory
from book_indexer.core.builder import build_book
from book_indexer.storage.sqlite import cleanup_missing_books
from book_indexer.storage.sqlite import get_book_file_info
from book_indexer.storage.sqlite import save_index_sqlite
from book_indexer.storage.search import search_books
from book_indexer.storage.sqlite import init_db
from book_indexer.storage.sqlite import mark_seen_bulk

DB_PATH = "index.db"


def index(path: str):
    init_db(DB_PATH)
    current_run = time.time()

    files = scan_directory(path)

    books = []
    paths = []
    unchanged = 0

    for f in files:
        paths.append(str(f))

        existing_meta = get_book_file_info(f, DB_PATH)
        book, status = build_book(f, existing_meta)

        if status == "unchanged":
            unchanged += 1

        if book:
            books.append(book)

    save_stats = save_index_sqlite(books, DB_PATH, path, current_run)

    mark_seen_bulk(paths, DB_PATH, current_run)

    removed = cleanup_missing_books(DB_PATH, path, current_run)

    print(f"+{save_stats['added']} added")
    print(f"~{save_stats['updated']} updated")
    print(f"-{removed} removed")
    print(f"={unchanged} unchanged")


def search(text: str):
    rows = search_books(DB_PATH, text)

    if not rows:
        print("No results found")
        return

    rows = rows[:20]

    for path, title, author in rows:
        title = title or "[no title]"
        author = author or "[no author]"
        author = " ".join(author.split()) if author else author

        print(f"{title} — {author}")
        print(f"  {path}")
        print()

def main():
    print("cli started")

    if len(sys.argv) < 2:
        print("commands: index | search")
        return

    cmd = sys.argv[1]

    if cmd == "index":
        if len(sys.argv) < 3:
            print("need path")
            return

        index(sys.argv[2])
    elif cmd == "search":
        search(sys.argv[2])


if __name__ == "__main__":
    main()
