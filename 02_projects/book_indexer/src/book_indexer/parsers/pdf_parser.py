from book_indexer.core.book import Book


def parse_pdf(book: Book):
    # пока просто используем имя файла
    book.title = book.name