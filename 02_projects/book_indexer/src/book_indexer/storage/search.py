import sqlite3


def _unicode_lower(value):
    if value is None:
        return None

    return str(value).casefold()


def search_books(db_path: str, text: str):
    conn = sqlite3.connect(db_path)
    conn.create_function("LOWER", 1, _unicode_lower)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT path, title, author, description
        FROM books
        WHERE
            LOWER(name) LIKE LOWER(?)
            OR LOWER(title) LIKE LOWER(?)
            OR LOWER(author) LIKE LOWER(?)
        """,
        (f"%{text}%", f"%{text}%", f"%{text}%"),
    )

    rows = cur.fetchall()

    conn.close()

    return rows


def get_book_by_query(db_path: str, text: str):
    rows = search_books(db_path, text)

    if not rows:
        return None

    rows = sorted(rows, key=lambda row: ((row[1] or "").lower(), row[0]))
    return rows[0]
