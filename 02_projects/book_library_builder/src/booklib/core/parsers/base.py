from dataclasses import dataclass


@dataclass
class ParseResult:
    status: str
    title: str | None = None
    author: str | None = None
    error: str | None = None
