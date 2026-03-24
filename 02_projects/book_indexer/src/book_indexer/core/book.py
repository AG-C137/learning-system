from pathlib import Path


class Book:
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.extension = path.suffix.lower()

        self.title = None
        self.author = None

    def __str__(self):
        return f"{self.name} ({self.extension})"