import sqlite3
from pathlib import Path

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
            user_notes TEXT,
            source_dir TEXT,
            size INTEGER,
            mtime REAL,
            last_seen REAL
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

    if "user_notes" not in columns:
        cur.execute("ALTER TABLE books ADD COLUMN user_notes TEXT")


def get_book_file_info(path, db_path):
    db_path = _normalize_path(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    _create_books_table(cur)
    _ensure_books_columns(cur)

    cur.execute(
        """
        SELECT size, mtime, description, user_notes
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
        "user_notes": row["user_notes"],
    }


def save_index_sqlite(books, db_path, source_dir, current_run):
    db_path = _normalize_path(db_path)
    source_dir = _normalize_path(source_dir)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _ensure_books_columns(cur)
    stats = {"added": 0, "updated": 0}

    for b in books:
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
                user_notes,
                source_dir,
                size,
                mtime,
                last_seen
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                book_path,
                b.name,
                b.extension,
                b.title,
                b.author,
                b.description,
                b.user_notes,
                source_dir,
                size,
                mtime,
                current_run,
            ),
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
    _ensure_books_columns(cur)

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
    _ensure_books_columns(cur)

    conn.commit()
    conn.close()


def mark_seen_bulk(paths, db_path, current_run):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    _create_books_table(cur)
    _ensure_books_columns(cur)

    cur.executemany(
        "UPDATE books SET last_seen = ? WHERE path = ?",
        [(current_run, str(p)) for p in paths],
    )

    conn.commit()
    conn.close()
