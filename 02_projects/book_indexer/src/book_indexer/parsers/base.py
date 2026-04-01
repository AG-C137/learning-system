from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from typing import Optional
from typing import Protocol


@dataclass
class ParseResult:
    title: Optional[str] = None
    author: Optional[str] = None
    status: Literal["ok", "partial", "failed"] = "ok"
    error: Optional[str] = None


class BaseParser(Protocol):
    def parse(self, path: Path) -> ParseResult:
        ...
