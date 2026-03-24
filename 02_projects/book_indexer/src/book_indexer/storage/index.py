import json
from pathlib import Path

from book_indexer.core.book import Book


def save_index(books: list[Book], path: str):
    data = []

    for b in books:
        data.append(
            {
                "name": b.name,
                "path": str(b.path),
                "ext": b.extension,
                "title": b.title,
                "author": b.author,
            }
        )

    out = Path(path)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)