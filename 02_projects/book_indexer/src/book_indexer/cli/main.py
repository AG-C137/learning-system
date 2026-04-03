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


def main():
    print("cli started")

    if len(sys.argv) < 2:
        print("commands: index | search | show")
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


if __name__ == "__main__":
    main()
