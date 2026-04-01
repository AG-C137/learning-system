from pathlib import Path

from book_indexer.core.book import Book
from book_indexer.parsers.registry import get_parser


def build_book(path: Path, existing_meta=None):
    st = path.stat()
    size = st.st_size
    mtime = st.st_mtime

    if existing_meta is not None:
        old_size, old_mtime = existing_meta
        if old_size == size and old_mtime == mtime:
            return None, "unchanged"

    book = Book(path)

    parser = get_parser(book.extension)

    if parser:
        result = parser.parse(path)
        if result.status != "failed":
            book.title = result.title
            book.author = result.author

    if existing_meta is None:
        return book, "added"

    return book, "updated"
