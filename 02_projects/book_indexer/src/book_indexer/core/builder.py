from pathlib import Path
import re

from book_indexer.ai.describer import generate_description
from book_indexer.core.book import Book
from book_indexer.parsers.registry import get_parser


def split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if current_len + len(sentence) > chunk_size and current:
            chunk = " ".join(current)
            chunks.append(chunk)

            overlap_sentences = current[-2:] if len(current) >= 2 else current
            current = overlap_sentences.copy()
            current_len = sum(len(s) for s in current)

        current.append(sentence)
        current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def normalize_text(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_book(path: Path, existing_meta=None):
    st = path.stat()
    size = st.st_size
    mtime = st.st_mtime
    book = Book(path)

    if existing_meta is not None:
        old_size = existing_meta["size"]
        old_mtime = existing_meta["mtime"]
        if (
            old_size == size
            and old_mtime == mtime
            and (
                (existing_meta.get("description") and existing_meta.get("raw_text"))
                or get_parser(book.extension) is None
                or book.extension == ".pdf"
            )
        ):
            return None, "unchanged"

    if existing_meta is not None:
        book.description = existing_meta["description"]
        book.raw_text = existing_meta.get("raw_text")
        book.user_notes = existing_meta["user_notes"]

    parser = get_parser(book.extension)

    if parser:
        try:
            result = parser.parse(path)
        except Exception:
            result = None

        if result is not None and result.status != "failed":
            book.title = result.title
            book.author = result.author

            if result.text:
                book.raw_text = normalize_text(result.text)

                print(f"[debug] raw_text_len={len(book.raw_text)}")

                sample = book.raw_text[:1000].lower()
                print(f"[debug] has_osteopat={ 'остеопат' in sample }")

                book.chunks = split_into_chunks(book.raw_text)
            else:
                book.raw_text = None
                book.chunks = []

            if not book.description and result.text:
                book.description = generate_description(result.text)

    if existing_meta is None:
        return book, "added"

    return book, "updated"
