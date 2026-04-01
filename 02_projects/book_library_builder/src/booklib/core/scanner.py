print("SCANNER LOADED")

from pathlib import Path
from dataclasses import dataclass
from booklib.core.parser import parse_name
from booklib.core.parsers import get_parser_for_path


ALLOWED_EXT = {
    ".pdf",
    ".djvu",
    ".epub",
    ".fb2",
    ".mobi",
    ".doc",
    ".docx",
}

ALLOWED_ARCHIVE_EXT = {
    ".zip",
}


@dataclass
class Book:

    path: str
    name: str
    ext: str
    size: int


def scan_folder(folder):

    books = []

    for p in Path(folder).rglob("*"):

        if not p.is_file():
            continue

        # skip hidden
        if any(part.startswith(".") for part in p.parts):
            continue

        ext = p.suffix.lower()
        name = p.name
        full = str(p)
        size = p.stat().st_size

        # normal books
        if ext in ALLOWED_EXT:
            pass

        # fb2.zip / epub.zip / pdf.zip
        elif ext in ALLOWED_ARCHIVE_EXT:

            if not any(name.lower().endswith(x + ".zip") for x in ALLOWED_EXT):
                continue

        else:
            continue

        author = None
        title = None

        parser = get_parser_for_path(full)
        if parser is not None:
            result = parser.parse(full)
            author = result.author
            title = result.title

        if not author and not title:
            author, title = parse_name(name)

        books.append(
            {
                "name": name,
                "author": author,
                "title": title,
                "path": full,
                "ext": ext,
                "size": size,
            }
        )

    return books
