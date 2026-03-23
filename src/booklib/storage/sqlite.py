import sqlite3
from pathlib import Path


DB_PATH = "data/index/books.db"


def get_conn():

    Path("data/index").mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def init_db():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        create table if not exists books (

            id integer primary key,

            name text,
            author text,
            title text,

            path text unique,

            ext text,
            size integer

        )
        """
    )

    conn.commit()
    conn.close()


def save_books(books):

    conn = get_conn()
    cur = conn.cursor()

    for b in books:

        cur.execute(
            """
            insert or ignore into books
            (name, author, title, path, ext, size)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                b["name"],
                b["author"],
                b["title"],
                b["path"],
                b["ext"],
                b["size"],
            ),
        )

    conn.commit()
    conn.close()


def search_books(field, words):

    conn = get_conn()
    cur = conn.cursor()

    sql = """
        select author, title, ext, path
        from books
        where 1=1
    """

    params = []

    for w in words:

        if field == "author":

            sql += " and lower(author) like ?"
            params.append(f"%{w.lower()}%")

        elif field == "title":

            sql += " and lower(title) like ?"
            params.append(f"%{w.lower()}%")

        elif field == "ext":

            sql += " and lower(ext) like ?"
            params.append(f"%{w.lower()}%")

        elif field == "any":

            sql += """
                and (
                    lower(author) like ?
                    or lower(title) like ?
                    or lower(name) like ?
                )
            """

            params.append(f"%{w.lower()}%")
            params.append(f"%{w.lower()}%")
            params.append(f"%{w.lower()}%")

    cur.execute(sql, params)

    rows = cur.fetchall()

    conn.close()

    return rows