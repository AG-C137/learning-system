from pathlib import Path


def detect_book_extension(path: Path) -> str:
    name = path.name.lower()

    if name.endswith(".fb2.zip"):
        return ".fb2.zip"

    return path.suffix.lower()


class Book:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.extension = detect_book_extension(path)

        self.title = None
        self.author = None
        self.description = None
        self.raw_text = None
        self.user_notes = None

    def __str__(self):
        return f"{self.name} ({self.extension})"
