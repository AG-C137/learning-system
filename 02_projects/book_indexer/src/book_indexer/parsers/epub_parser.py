from html.parser import HTMLParser
from pathlib import Path
from posixpath import dirname
from posixpath import join
from posixpath import normpath
import zipfile
import xml.etree.ElementTree as ET

from .base import ParseResult

TEXT_LIMIT = 15_000


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "div", "br", "li"):
            self.parts.append("\n")

    def handle_data(self, data: str):
        cleaned = " ".join(data.split())
        if cleaned:
            self.parts.append(cleaned)

    def get_text(self) -> str:
        text = "".join(self.parts)
        return text.strip()


class EPUBParser:
    def parse(self, path: Path) -> ParseResult:
        try:
            with zipfile.ZipFile(path) as z:
                # container.xml
                data = z.read("META-INF/container.xml")
                root = ET.fromstring(data)

                rootfile = root.find(
                    ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
                )
                if rootfile is None:
                    return ParseResult(status="failed")

                opf_path = rootfile.attrib.get("full-path")
                if not opf_path:
                    return ParseResult(status="failed")

                # OPF
                opf_data = z.read(opf_path)
                root = ET.fromstring(opf_data)
                package_ns = self._package_namespace(root)

                # metadata
                title_el = root.find(
                    ".//{http://purl.org/dc/elements/1.1/}title"
                )
                author_el = root.find(
                    ".//{http://purl.org/dc/elements/1.1/}creator"
                )

                title = title_el.text.strip() if title_el is not None and title_el.text else None
                author = author_el.text.strip() if author_el is not None and author_el.text else None
                text = self._extract_spine_text(z, root, opf_path, package_ns)

                status = "ok" if title else "partial"

                return ParseResult(
                    title=title,
                    author=author,
                    text=text,
                    status=status,
                )

        except Exception as e:
            print(f"epub parse error: {path} {e}")
            return ParseResult(status="failed", error=str(e))

    def _package_namespace(self, root: ET.Element) -> str:
        if root.tag.startswith("{"):
            return root.tag.split("}", 1)[0] + "}"

        return ""

    def _extract_spine_text(
        self,
        archive: zipfile.ZipFile,
        root: ET.Element,
        opf_path: str,
        package_ns: str,
    ) -> str | None:
        manifest = {}

        for item in root.findall(f".//{package_ns}manifest/{package_ns}item"):
            item_id = item.attrib.get("id")
            href = item.attrib.get("href")
            if item_id and href:
                manifest[item_id] = href

        base_dir = dirname(opf_path)
        parts: list[str] = []
        total = 0
        chunks = 0

        for itemref in root.findall(f".//{package_ns}spine/{package_ns}itemref"):
            item_id = itemref.attrib.get("idref")
            href = manifest.get(item_id)

            if not href:
                continue
            if any(
                marker in href.lower()
                for marker in (
                    "toc",
                    "nav",
                    "contents",
                    "cover",
                    "titlepage",
                    "copyright",
                    "imprint",
                )
            ):
                continue

            member_path = normpath(join(base_dir, href))

            try:
                html_data = archive.read(member_path)
            except KeyError:
                continue

            text = self._strip_html(html_data)
            if not text or len(text) < 200:
                continue

            words = text.split()
            if len(words) < 50:
                continue

            lower_text = text.lower()
            if lower_text.count("\n") > 20 and any(
                x in lower_text for x in ["глава", "chapter", "contents"]
            ):
                continue

            remaining = TEXT_LIMIT - total
            if remaining <= 0:
                break

            piece = text[:remaining]
            parts.append(piece)
            total += len(piece) + 1
            chunks += 1

            if chunks >= 5:
                break

            if total >= TEXT_LIMIT and chunks >= 1:
                break

        result = " ".join(parts).strip()

        return result or None

    def _strip_html(self, html_data: bytes) -> str:
        parser = _HTMLTextExtractor()
        parser.feed(html_data.decode("utf-8", errors="ignore"))
        parser.close()
        return parser.get_text()
