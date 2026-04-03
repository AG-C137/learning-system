from pathlib import Path

from book_indexer.ai.describer import generate_description
from book_indexer.core.book import Book
from book_indexer.parsers.registry import get_parser


def build_book(path: Path, existing_meta=None):
    st = path.stat()
    size = st.st_size
    mtime = st.st_mtime
    book = Book(path)

    if existing_meta is not None:
        old_size = existing_meta["size"]
        old_mtime = existing_meta["mtime"]
        if (
            old_size == size
            and old_mtime == mtime
            and (
                existing_meta["description"]
                or get_parser(book.extension) is None
                or book.extension == ".pdf"
            )
        ):
            return None, "unchanged"

    if existing_meta is not None:
        book.description = existing_meta["description"]
        book.user_notes = existing_meta["user_notes"]

    parser = get_parser(book.extension)

    if parser:
        try:
            result = parser.parse(path)
        except Exception:
            result = None

        if result is not None and result.status != "failed":
            book.title = result.title
            book.author = result.author

            if not book.description and result.text:
                book.description = generate_description(result.text)

    if existing_meta is None:
        return book, "added"

    return book, "updated"
