import sys

from booklib.core.scanner import scan_folder
from booklib.core.config import load_sources
from booklib.storage.sqlite import init_db, save_books, search_books


CONFIG = "config/sources.json"


def build():

    init_db()

    sources = load_sources(CONFIG)

    all_books = []

    for path in sources:

        print("SCAN:", path)

        try:
            books = scan_folder(path)
        except Exception as e:
            print("ERROR:", e)
            continue

        print("found:", len(books))

        all_books.extend(books)

    save_books(all_books)

    print("DB SAVED")


def search(args):

    if len(args) < 2:
        print("usage: search field words...")
        return

    field = args[0]
    words = args[1:]

    rows = search_books(field, words)

    for r in rows:
        print(r)


def main():

    if len(sys.argv) > 1:

        if sys.argv[1] == "search":
            search(sys.argv[2:])
            return

    build()


if __name__ == "__main__":
    main()