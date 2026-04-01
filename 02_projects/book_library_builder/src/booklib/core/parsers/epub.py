import zipfile
import xml.etree.ElementTree as ET

from .base import ParseResult


class EPUBParser:

    def parse(self, path):
        with zipfile.ZipFile(path) as z:
            data = z.read("META-INF/container.xml")
            root = ET.fromstring(data)

            rootfile = root.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
            opf_path = rootfile.attrib["full-path"]

            opf_data = z.read(opf_path)
            root = ET.fromstring(opf_data)

            title_el = root.find(".//{http://purl.org/dc/elements/1.1/}title")
            author_el = root.find(".//{http://purl.org/dc/elements/1.1/}creator")

            title = title_el.text.strip() if title_el is not None else None
            author = author_el.text.strip() if author_el is not None else None

        return ParseResult(
            title=title,
            author=author,
            status="ok" if title else "partial",
        )
