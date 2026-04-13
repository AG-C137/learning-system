from __future__ import annotations

import sqlite3
from pathlib import Path

from book_indexer.models import Book


def _fetch_authors(cursor: sqlite3.Cursor, book_id: int) -> list[str]:
    try:
        cursor.execute(
            """
            SELECT a.name
            FROM books_authors_link bal
            JOIN authors a ON a.id = bal.author
            WHERE bal.book = ?
            """,
            (book_id,),
        )
    except sqlite3.Error:
        return []

    authors: list[str] = []
    for row in cursor.fetchall():
        if not row:
            continue
        name = row[0]
        if isinstance(name, str) and name:
            authors.append(name)
    return authors


def _fetch_tags(cursor: sqlite3.Cursor, book_id: int) -> list[str]:
    try:
        cursor.execute(
            """
            SELECT t.name
            FROM books_tags_link btl
            JOIN tags t ON t.id = btl.tag
            WHERE btl.book = ?
            """,
            (book_id,),
        )
    except sqlite3.Error:
        return []

    tags: list[str] = []
    for row in cursor.fetchall():
        if not row:
            continue
        name = row[0]
        if isinstance(name, str) and name:
            tags.append(name)
    return tags


def _fetch_series(cursor: sqlite3.Cursor, book_id: int) -> str | None:
    try:
        cursor.execute(
            """
            SELECT s.name
            FROM books_series_link bsl
            JOIN series s ON s.id = bsl.series
            WHERE bsl.book = ?
            LIMIT 1
            """,
            (book_id,),
        )
    except sqlite3.Error:
        return None

    row = cursor.fetchone()
    if not row:
        return None
    name = row[0]
    if isinstance(name, str) and name:
        return name
    return None


def _pick_file_entry(cursor: sqlite3.Cursor, book_id: int) -> tuple[str, str] | None:
    try:
        cursor.execute(
            """
            SELECT format, name
            FROM data
            WHERE book = ?
            """,
            (book_id,),
        )
    except sqlite3.Error:
        return None

    entries: list[tuple[str, str]] = []
    for fmt, name in cursor.fetchall():
        if not isinstance(fmt, str) or not isinstance(name, str):
            continue
        fmt_clean = fmt.strip().lstrip(".").lower()
        name_clean = str(name).strip()
        if not fmt_clean or not name_clean:
            continue
        entries.append((fmt_clean, name_clean))

    if not entries:
        return None

    for entry in entries:
        if entry[0] == "epub":
            return entry
    return entries[0]


def load_calibre_books(db_path: str, library_path: str) -> list[Book]:
    books: list[Book] = []
    library_root = Path(library_path)

    try:
        connection = sqlite3.connect(db_path)
    except sqlite3.Error:
        return books

    with connection:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT id, title, path FROM books")
            rows = cursor.fetchall()
        except sqlite3.Error:
            return books

        for row in rows:
            try:
                if not row or len(row) < 2:
                    continue

                book_id = row[0]
                title = row[1]

                if book_id is None or not isinstance(title, str) or not title:
                    continue

                file_entry = _pick_file_entry(cursor, int(book_id))
                if file_entry is None:
                    continue

                fmt, filename_base = file_entry

                filename = f"{filename_base}.{fmt}"

                authors = _fetch_authors(cursor, int(book_id))
                tags = _fetch_tags(cursor, int(book_id))
                series = _fetch_series(cursor, int(book_id))

                book_rel_path = row[2]

                if book_rel_path:
                    file_path = library_root / Path(book_rel_path) / filename
                else:
                    author_dir = authors[0] if authors else "Unknown"
                    file_path = library_root / author_dir / title / filename

                
                if not Path(file_path).exists():
                    print("MISSING:", file_path)
                    continue
                    

                books.append(
                    Book(
                        id=str(book_id),
                        title=title,
                        authors=authors,
                        path=str(file_path),
                        format=fmt,
                        tags=tags,
                        series=series,
                        chapters=[],
                    )
                )
            except Exception as e:
                print("ERROR:", e)
                print("ROW:", row)
                raise

    return books
