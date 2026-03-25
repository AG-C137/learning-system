import sys

from book_indexer.scan.filesystem import scan_directory
from book_indexer.core.builder import build_book
from book_indexer.storage.sqlite import save_index_sqlite
from book_indexer.storage.search import search_books
from book_indexer.storage.sqlite import init_db

DB_PATH = "index.db"

def index(path: str):
    init_db(DB_PATH)

    files = scan_directory(path)

    print("FILES =", files)   # ← добавить

    books = []

    for f in files:
        books.append(build_book(f, DB_PATH))

    save_index_sqlite(books, DB_PATH, path)


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