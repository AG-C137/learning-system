from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import Protocol


@dataclass
class ParseResult:
    title: Optional[str] = None
    author: Optional[str] = None
    text: Optional[str] = None
    status: Literal["ok", "partial", "failed"] = "ok"
    error: Optional[str] = None


class BaseParser(Protocol):
    def parse(self, path: Path) -> ParseResult:
        ...
def clean_book_text(text: str) -> str:
    if not text:
        return ""

    # убрать лишние пробелы
    text = " ".join(text.split())

    # удалить короткие мусорные строки
    parts = text.split(". ")
    parts = [p for p in parts if len(p) > 40]

    text = ". ".join(parts)

    return text.strip()