from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    id: str
    book_id: str
    chapter_id: str
    text: str
    embedding: Optional[list[float]] = None
    position: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "chapter_id": self.chapter_id,
            "text": self.text,
            "embedding": self.embedding,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(
            id=data["id"],
            book_id=data["book_id"],
            chapter_id=data["chapter_id"],
            text=data["text"],
            embedding=data.get("embedding"),
            position=data.get("position", 0),
        )


@dataclass
class Chapter:
    id: str
    book_id: str
    title: Optional[str]
    order: int
    text: Optional[str]
    chunks: list[Chunk] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "book_id": self.book_id,
            "title": self.title,
            "order": self.order,
            "text": self.text,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chapter":
        return cls(
            id=data["id"],
            book_id=data["book_id"],
            title=data.get("title"),
            order=data["order"],
            text=data.get("text"),
            chunks=[Chunk.from_dict(chunk) for chunk in data.get("chunks", [])],
        )


@dataclass
class Book:
    id: str
    title: str
    authors: list[str] = field(default_factory=list)
    path: str = ""
    format: str = ""
    language: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    series: Optional[str] = None
    description: Optional[str] = None
    chapters: list[Chapter] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": list(self.authors),
            "path": self.path,
            "format": self.format,
            "language": self.language,
            "tags": list(self.tags),
            "series": self.series,
            "description": self.description,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Book":
        return cls(
            id=data["id"],
            title=data["title"],
            authors=list(data.get("authors") or []),
            path=data.get("path", ""),
            format=data.get("format", ""),
            language=data.get("language"),
            tags=list(data.get("tags") or []),
            series=data.get("series"),
            description=data.get("description"),
            chapters=[Chapter.from_dict(chapter) for chapter in data.get("chapters", [])],
        )
