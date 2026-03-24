import sys

from book_indexer.scan.filesystem import scan_directory
from book_indexer.core.builder import build_book
from book_indexer.storage.sqlite import save_index_sqlite
from book_indexer.storage.search import search_books

DB_PATH = "index.db"

def index(path: str):
    files = scan_directory(path)

    books = []

    for f in files:
        books.append(build_book(f))

    save_index_sqlite(books, "./index.db", path)


def search(text: str):
    rows = search_books("index.db", text)

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