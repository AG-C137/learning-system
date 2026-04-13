import json
import sqlite3

from book_indexer.models import Book


class BookStorage:
    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id TEXT PRIMARY KEY,
                title TEXT,
                authors TEXT,
                path TEXT,
                format TEXT,
                tags TEXT,
                series TEXT,
                description TEXT
            )
            """
        )
        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_books_title ON books(title)
            """
        )
        self.connection.commit()

    def save_books(self, books: list[Book]) -> None:
        rows = [
            (
                book.id,
                book.title,
                json.dumps(book.authors),
                book.path,
                book.format,
                json.dumps(book.tags),
                book.series,
                book.description,
            )
            for book in books
        ]

        self.connection.executemany(
            """
            INSERT OR REPLACE INTO books (
                id,
                title,
                authors,
                path,
                format,
                tags,
                series,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def load_books(self) -> list[Book]:
        cursor = self.connection.execute(
            """
            SELECT id, title, authors, path, format, tags, series, description
            FROM books
            """
        )

        books = []
        for row in cursor.fetchall():
            books.append(
                Book(
                    id=row["id"],
                    title=row["title"],
                    authors=json.loads(row["authors"]) if row["authors"] else [],
                    path=row["path"] or "",
                    format=row["format"] or "",
                    tags=json.loads(row["tags"]) if row["tags"] else [],
                    series=row["series"],
                    description=row["description"],
                    chapters=[],
                )
            )

        return books

    def close(self) -> None:
        self.connection.close()
