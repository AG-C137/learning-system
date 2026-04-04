import json
import sqlite3
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

from book_indexer.core.book import Book


def _normalize_path(path: str) -> str:
    return str(Path(path).resolve())


def _create_books_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            path TEXT PRIMARY KEY,
            name TEXT,
            ext TEXT,
            title TEXT,
            author TEXT,
            description TEXT,
            raw_text TEXT,
            user_notes TEXT,
            source_dir TEXT,
            size INTEGER,
            mtime REAL,
            last_seen REAL
        )
        """
    )


def _create_book_chunks_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS book_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_path TEXT,
            chunk_index INTEGER,
            text TEXT,
            embedding TEXT
        )
        """
    )


def _ensure_books_columns(cur):
    cur.execute("PRAGMA table_info(books)")
    columns = {row[1] for row in cur.fetchall()}

    if "last_seen" not in columns:
        cur.execute("ALTER TABLE books ADD COLUMN last_seen REAL")

    if "description" not in columns:
        cur.execute("ALTER TABLE books ADD COLUMN description TEXT")

    if "raw_text" not in columns:
        cur.execute("ALTER TABLE books ADD COLUMN raw_text TEXT")

    if "user_notes" not in columns:
        cur.execute("ALTER TABLE books ADD COLUMN user_notes TEXT")


def _ensure_book_chunks_columns(cur):
    cur.execute("PRAGMA table_info(book_chunks)")
    columns = {row[1] for row in cur.fetchall()}

    if "embedding" not in columns:
        cur.execute("ALTER TABLE book_chunks ADD COLUMN embedding TEXT")


def get_embedding(text: str) -> list[float] | None:
    payload = json.dumps(
        {
            "model": "nomic-embed-text",
            "prompt": text[:1000],
        }
    ).encode("utf-8")

    request = Request(
        "http://localhost:11434/api/embeddings",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except (OSError, URLError, TimeoutError, ValueError):
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None

    return data.get("embedding")


def get_book_file_info(path, db_path):
    db_path = _normalize_path(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    _create_books_table(cur)
    _ensure_books_columns(cur)

    cur.execute(
        """
        SELECT size, mtime, description, raw_text, user_notes
        FROM books
        WHERE path = ?
        """,
        (str(path),),
    )

    row = cur.fetchone()

    conn.close()
    if row is None:
        return None

    return {
        "size": row["size"],
        "mtime": row["mtime"],
        "description": row["description"],
        "raw_text": row["raw_text"] if "raw_text" in row.keys() else None,
        "user_notes": row["user_notes"],
    }


def save_index_sqlite(books_with_status, db_path, source_dir, current_run):
    db_path = _normalize_path(db_path)
    source_dir = _normalize_path(source_dir)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _create_book_chunks_table(cur)
    _ensure_books_columns(cur)
    _ensure_book_chunks_columns(cur)
    stats = {"added": 0, "updated": 0}

    for b, status in books_with_status:
        p = Path(b.path)
        st = p.stat()

        size = st.st_size
        mtime = st.st_mtime
        book_path = str(b.path)

        cur.execute(
            """
            SELECT 1
            FROM books
            WHERE path = ?
            """,
            (book_path,),
        )

        if cur.fetchone() is None:
            stats["added"] += 1
        else:
            stats["updated"] += 1

        cur.execute(
            """
            INSERT OR REPLACE INTO books(
                path,
                name,
                ext,
                title,
                author,
                description,
                raw_text,
                user_notes,
                source_dir,
                size,
                mtime,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_path,
                b.name,
                b.extension,
                b.title,
                b.author,
                b.description,
                b.raw_text,
                b.user_notes,
                source_dir,
                size,
                mtime,
                current_run,
            ),
        )

        if status in ("added", "updated"):
            cur.execute(
                "DELETE FROM book_chunks WHERE book_path = ?",
                (book_path,),
            )

            for i, chunk in enumerate(getattr(b, "chunks", [])):
                cur.execute(
                    "INSERT INTO book_chunks (book_path, chunk_index, text) VALUES (?, ?, ?)",
                    (book_path, i, chunk),
                )

    cur.execute(
        "SELECT id, text FROM book_chunks WHERE embedding IS NULL"
    )
    rows = cur.fetchall()

    for row_id, text in rows:
        embedding = get_embedding(text)
        if embedding:
            cur.execute(
                "UPDATE book_chunks SET embedding = ? WHERE id = ?",
                (json.dumps(embedding), row_id),
            )

    conn.commit()
    conn.close()
    return stats


def cleanup_missing_books(db_path, source_dir, current_run):
    db_path = _normalize_path(db_path)
    source_dir = _normalize_path(source_dir)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _create_book_chunks_table(cur)
    _ensure_books_columns(cur)
    _ensure_book_chunks_columns(cur)

    cur.execute(
        """
        DELETE FROM books
        WHERE source_dir = ?
          AND (last_seen IS NULL OR last_seen < ?)
        """,
        (source_dir, current_run),
    )

    removed = cur.rowcount

    conn.commit()
    conn.close()
    return removed


def init_db(db_path):
    db_path = _normalize_path(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _create_book_chunks_table(cur)
    _ensure_books_columns(cur)
    _ensure_book_chunks_columns(cur)

    conn.commit()
    conn.close()


def mark_seen_bulk(paths, db_path, current_run):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _create_book_chunks_table(cur)
    _ensure_books_columns(cur)
    _ensure_book_chunks_columns(cur)

    cur.executemany(
        "UPDATE books SET last_seen = ? WHERE path = ?",
        [(current_run, str(p)) for p in paths],
    )

    conn.commit()
    conn.close()
