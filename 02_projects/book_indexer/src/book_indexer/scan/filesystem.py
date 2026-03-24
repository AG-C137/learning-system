from pathlib import Path


BOOK_EXTENSIONS = {
    ".pdf",
    ".fb2",
    ".epub",
    ".txt",
    ".djvu",
    ".doc",
    ".docx",
}


def scan_directory(path: str):
    base = Path(path)

    result = []

    for file in base.rglob("*"):
        if not file.is_file():
            continue

        if file.suffix.lower() in BOOK_EXTENSIONS:
            result.append(file)

    return result