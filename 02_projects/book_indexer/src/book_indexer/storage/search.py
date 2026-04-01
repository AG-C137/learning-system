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
        SELECT path, title, author
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
