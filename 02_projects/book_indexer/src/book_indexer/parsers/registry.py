from book_indexer.parsers.base import BaseParser
from book_indexer.parsers.fb2_parser import FB2Parser
from book_indexer.parsers.pdf_parser import PDFParser
from .epub_parser import EPUBParser


PARSERS = {
    ".fb2": FB2Parser(),
    ".fb2.zip": FB2Parser(),
    ".epub": EPUBParser(),
    ".pdf": PDFParser(),
}


def get_parser(ext: str) -> BaseParser | None:
    return PARSERS.get(ext)
