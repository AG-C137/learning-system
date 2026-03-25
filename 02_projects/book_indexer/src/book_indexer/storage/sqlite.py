import sqlite3
from pathlib import Path

from book_indexer.core.book import Book


def save_index_sqlite(books, db_path, source_dir):
    db_path = str(Path(db_path).resolve())

    print("DB PATH =", db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            path TEXT PRIMARY KEY,
            name TEXT,
            ext TEXT,
            title TEXT,
            author TEXT,
            source_dir TEXT
        )
        """
    )

    # ✅ NEW — clean old records for this source
    cur.execute(
        "DELETE FROM books WHERE source_dir = ?",
        (str(source_dir),),
    )

    # insert new records
    for b in books:
        cur.execute(
            """
            INSERT OR REPLACE INTO books(path, name, ext, title, author, source_dir)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(b.path),
                b.name,
                b.extension,
                b.title,
                b.author,
                str(source_dir),
            ),
        )

    conn.commit()
    conn.close()