import sys
import time

from book_indexer.scan.filesystem import scan_directory
from book_indexer.core.builder import build_book
from book_indexer.storage.sqlite import cleanup_missing_books
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

    for f in files:
        paths.append(str(f))

        book = build_book(f, DB_PATH)
        if book:
            books.append(book)

    save_index_sqlite(books, DB_PATH, path, current_run)

    mark_seen_bulk(paths, DB_PATH, current_run)

    cleanup_missing_books(DB_PATH, path, current_run)

def search(text: str):
    rows = search_books(DB_PATH, text)

    for r in rows:
        print(r)


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
