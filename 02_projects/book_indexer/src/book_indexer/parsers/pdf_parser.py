from pathlib import Path

from book_indexer.parsers.base import ParseResult


class PDFParser:
    def parse(self, path: Path) -> ParseResult:
        # пока просто используем имя файла
        return ParseResult(title=path.stem, text=None, status="partial")
