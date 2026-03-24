import json
from dataclasses import asdict
from pathlib import Path


def save_index(books, path):

    data = [asdict(b) for b in books]

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)