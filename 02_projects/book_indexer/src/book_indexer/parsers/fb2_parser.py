import xml.etree.ElementTree as ET

from book_indexer.core.book import Book


def parse_fb2(book: Book):
    try:
        tree = ET.parse(book.path)
        root = tree.getroot()

        title = root.find(".//book-title")
        if title is not None:
            book.title = title.text

        first = root.find(".//first-name")
        last = root.find(".//last-name")

        if first is not None and last is not None:
            book.author = f"{first.text} {last.text}"

    except Exception as e:
        print("fb2 parse error:", book.path, e)