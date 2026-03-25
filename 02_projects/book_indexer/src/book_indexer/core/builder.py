from pathlib import Path

from book_indexer.core.book import Book
from book_indexer.parsers.registry import get_parser



def build_book(path: Path, db_path: str):
    book = Book(path)

    parser = get_parser(book.extension)

    if parser:
        parser(book)

    return book