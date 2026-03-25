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
            source_dir TEXT,
            size INTEGER,
            mtime REAL
        )
        """
    )

    for b in books:

        p = Path(b.path)
        st = p.stat()

        size = st.st_size
        mtime = st.st_mtime

        cur.execute(
            """
            INSERT OR REPLACE INTO books(
                path,
                name,
                ext,
                title,
                author,
                source_dir,
                size,
                mtime
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(b.path),
                b.name,
                b.extension,
                b.title,
                b.author,
                str(source_dir),
                size,
                mtime,
            ),
        )

    conn.commit()
    conn.close()

def init_db(db_path):
    db_path = str(Path(db_path).resolve())

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
            source_dir TEXT,
            size INTEGER,
            mtime REAL
        )
        """
    )

    conn.commit()
    conn.close()