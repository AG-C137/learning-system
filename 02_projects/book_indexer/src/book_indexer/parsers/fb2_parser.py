import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

from book_indexer.parsers.base import ParseResult
from .base import clean_book_text

TEXT_LIMIT = 15_000


class FB2Parser:
    def parse(self, path: Path) -> ParseResult:
        try:
            tree = self._load_tree(path)
            root = tree.getroot()

            if root is None:
                return ParseResult(status="failed")

            ns = self._detect_namespace(root)

            title = None
            author = None

            # --- title ---
            title_node = root.find(f".//{ns}book-title")
            if title_node is not None and title_node.text:
                title = title_node.text.strip()

            # --- author ---
            first = root.find(f".//{ns}author/{ns}first-name")
            last = root.find(f".//{ns}author/{ns}last-name")

            first_text = first.text.strip() if first is not None and first.text else None
            last_text = last.text.strip() if last is not None and last.text else None

            if first_text and last_text:
                author = f"{first_text} {last_text}"

            # --- text ---
            text = self._extract_body_text(root, ns)

            status = "ok" if title else "partial"

            return ParseResult(
                title=title,
                author=author,
                text=text,
                status=status,
            )

        except Exception as e:
            print("fb2 parse error:", path, e)
            return ParseResult(status="failed", error=str(e))

    def _load_tree(self, path: Path) -> ET.ElementTree:
        if str(path).lower().endswith(".fb2.zip"):
            return self._load_tree_from_zip(path)

        return ET.parse(path)

    def _load_tree_from_zip(self, path: Path) -> ET.ElementTree:
        with zipfile.ZipFile(path) as archive:
            fb2_name = self._find_first_fb2_member(archive)
            if fb2_name is None:
                raise ValueError("No .fb2 file found inside archive")

            with archive.open(fb2_name) as fb2_file:
                data = fb2_file.read()

        root = ET.fromstring(data)
        return ET.ElementTree(root)

    def _find_first_fb2_member(self, archive: zipfile.ZipFile) -> str | None:
        for name in archive.namelist():
            if name.lower().endswith(".fb2"):
                return name
        return None

    def _detect_namespace(self, root: ET.Element) -> str:
        if root.tag.startswith("{"):
            return root.tag.split("}", 1)[0] + "}"
        return ""

    def _extract_body_text(self, root: ET.Element, ns: str) -> str | None:
        bodies = root.findall(f".//{ns}body")

        parts: list[str] = []
        total = 0

        for body in bodies:
            for chunk in body.itertext():
                cleaned = " ".join(chunk.split())
                if not cleaned:
                    continue

                remaining = TEXT_LIMIT - total
                if remaining <= 0:
                    break

                piece = cleaned[:remaining]
                parts.append(piece)
                total += len(piece) + 1

            if total >= TEXT_LIMIT:
                break

        text = " ".join(parts).strip()

        # 🔹 очистка текста
        text = clean_book_text(text)

        return text or None