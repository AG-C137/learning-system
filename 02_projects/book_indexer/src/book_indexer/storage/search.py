import sqlite3


def search_books(db_path: str, text: str):
    conn = sqlite3.connect(db_path)

    cur = conn.cursor()

    cur.execute(
        """
        SELECT path, title, author
        FROM books
        WHERE
            name LIKE ?
            OR title LIKE ?
            OR author LIKE ?
        """,
        (f"%{text}%", f"%{text}%", f"%{text}%"),
    )

    rows = cur.fetchall()

    conn.close()

    return rows