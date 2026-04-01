import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

from book_indexer.parsers.base import ParseResult


class FB2Parser:
    def parse(self, path: Path) -> ParseResult:
        try:
            tree = self._load_tree(path)
            root = tree.getroot()
            ns = self._detect_namespace(root)

            title = None
            author = None

            title_node = root.find(f".//{ns}book-title")
            if title_node is not None:
                title = title_node.text

            first = root.find(f".//{ns}author/{ns}first-name")
            last = root.find(f".//{ns}author/{ns}last-name")

            if first is not None and last is not None:
                author = f"{first.text} {last.text}"

            status = "ok" if title else "partial"
            return ParseResult(title=title, author=author, status=status)
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
