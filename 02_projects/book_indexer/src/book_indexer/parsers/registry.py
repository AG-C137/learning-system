from book_indexer.parsers.fb2_parser import parse_fb2
from book_indexer.parsers.pdf_parser import parse_pdf


PARSERS = {
    ".fb2": parse_fb2,
    ".pdf": parse_pdf,
}


def get_parser(ext: str):
    return PARSERS.get(ext)