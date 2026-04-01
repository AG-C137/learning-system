from pathlib import Path

from book_indexer.core.book import detect_book_extension


BOOK_EXTENSIONS = {
    ".pdf",
    ".fb2",
    ".epub",
    ".txt",
    ".djvu",
    ".doc",
    ".docx",
    ".fb2.zip"
}


def scan_directory(path: str):
    base = Path(path)

    result = []

    for file in base.rglob("*"):
        if not file.is_file():
            continue

        if detect_book_extension(file) in BOOK_EXTENSIONS:
            result.append(file)

    return result
