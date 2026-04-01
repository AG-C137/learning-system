from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from .base import ParseResult


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

                # metadata
                title_el = root.find(
                    ".//{http://purl.org/dc/elements/1.1/}title"
                )
                author_el = root.find(
                    ".//{http://purl.org/dc/elements/1.1/}creator"
                )

                title = title_el.text.strip() if title_el is not None and title_el.text else None
                author = author_el.text.strip() if author_el is not None and author_el.text else None

                status = "ok" if title else "partial"

                return ParseResult(
                    title=title,
                    author=author,
                    status=status,
                )

        except Exception as e:
            print(f"epub parse error: {path} {e}")
            return ParseResult(status="failed")