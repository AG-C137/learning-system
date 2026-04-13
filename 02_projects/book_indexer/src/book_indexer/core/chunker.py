from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from posixpath import dirname, join, normpath
import xml.etree.ElementTree as ET
import zipfile

from book_indexer.models import Book, Chunk


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)

    def get_text(self) -> str:
        return " ".join("".join(self.parts).split())


def _read_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _strip_html(html_text: str) -> str:
    import re

    parser = _HTMLTextExtractor()
    parser.feed(html_text)
    parser.close()

    text = parser.get_text()

    text = re.sub(r"\{[^}]*\}", " ", text)
    text = re.sub(r"[^\w\s]{2,}", " ", text)

    # 👇 новый слой
    text = re.sub(r"\b(Cover@page|Converted Ebook|page|body)\b", " ", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _read_epub_with_ebooklib(path: Path) -> str:
    try:
        from ebooklib import ITEM_DOCUMENT  # type: ignore
        from ebooklib import epub  # type: ignore
    except ImportError:
        return ""

    try:
        book = epub.read_epub(str(path))
    except Exception:
        return ""

    parts: list[str] = []
    for item in book.get_items():
        if item.get_type() != ITEM_DOCUMENT:
            continue

        try:
            content = item.get_content()
        except Exception:
            continue

        if isinstance(content, bytes):
            html_text = content.decode("utf-8", errors="ignore")
        else:
            html_text = str(content)

        text = _strip_html(html_text)
        if text:
            parts.append(text)

    return "\n\n".join(parts).strip()


def _package_namespace(root: ET.Element) -> str:
    if root.tag.startswith("{"):
        return root.tag.split("}", 1)[0] + "}"
    return ""


def _read_epub_from_zip(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            container_data = archive.read("META-INF/container.xml")
            container_root = ET.fromstring(container_data)

            rootfile = container_root.find(
                ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
            )
            if rootfile is None:
                return ""

            opf_path = rootfile.attrib.get("full-path")
            if not opf_path:
                return ""

            opf_data = archive.read(opf_path)
            package_root = ET.fromstring(opf_data)
            package_ns = _package_namespace(package_root)

            manifest: dict[str, str] = {}
            for item in package_root.findall(f".//{package_ns}manifest/{package_ns}item"):
                item_id = item.attrib.get("id")
                href = item.attrib.get("href")
                if item_id and href:
                    manifest[item_id] = href

            base_dir = dirname(opf_path)
            parts: list[str] = []

            for itemref in package_root.findall(f".//{package_ns}spine/{package_ns}itemref"):
                item_id = itemref.attrib.get("idref")
                href = manifest.get(item_id)
                if not href:
                    continue

                member_path = normpath(join(base_dir, href))
                try:
                    html_data = archive.read(member_path)
                except KeyError:
                    continue

                text = _strip_html(html_data.decode("utf-8", errors="ignore"))
                if text:
                    parts.append(text)

            return "\n\n".join(parts).strip()
    except Exception:
        return ""


def _read_epub(path: Path) -> str:
    text = _read_epub_with_ebooklib(path)
    if text:
        return text
    return _read_epub_from_zip(path)


def _extract_text(book: Book) -> str:
    path = Path(book.path)
    extension = path.suffix.lower()
    fmt = book.format.lower().lstrip(".")

    if extension == ".txt" or fmt == "txt":
        return _read_txt(path)
    if extension == ".epub" or fmt == "epub":
        return _read_epub(path)
    return ""


def _chunk_words(words: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not words:
        return []

    size = max(1, chunk_size)
    step = max(1, size - max(0, min(overlap, size - 1)))

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + size
        chunk_text = " ".join(words[start:end]).strip()
        if chunk_text:
            chunks.append(chunk_text)
        start += step

    return chunks


def chunk_book(book: Book, chunk_size: int = 500, overlap: int = 50) -> list[Chunk]:
    text = _extract_text(book)
    if not text:
        return []

    words = text.split()
    chunk_texts = _chunk_words(words, chunk_size=chunk_size, overlap=overlap)

    chunks: list[Chunk] = []
    for index, chunk_text in enumerate(chunk_texts):
        chunks.append(
            Chunk(
                id=f"{book.id}_{index}",
                book_id=book.id,
                chapter_id="",
                text=chunk_text,
                embedding=None,
                position=index,
            )
        )

    return chunks
