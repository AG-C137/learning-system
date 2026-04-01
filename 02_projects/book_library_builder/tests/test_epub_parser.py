import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.append(str(SRC_ROOT))


from booklib.core.parsers import EPUBParser, get_parser


class EPUBParserTests(unittest.TestCase):

    def test_extracts_title_and_author_from_opf(self):

        epub_path = self._create_epub(
            title="Example Book",
            author="Jane Doe",
        )

        result = EPUBParser().parse(str(epub_path))

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.title, "Example Book")
        self.assertEqual(result.author, "Jane Doe")

    def test_returns_partial_when_only_author_exists(self):

        epub_path = self._create_epub(author="Jane Doe")

        result = EPUBParser().parse(str(epub_path))

        self.assertEqual(result.status, "partial")
        self.assertIsNone(result.title)
        self.assertEqual(result.author, "Jane Doe")

    def test_registry_contains_epub_parser(self):

        self.assertIsInstance(get_parser(".epub"), EPUBParser)

    def _create_epub(self, title=None, author=None):

        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)

        epub_path = Path(tmpdir.name) / "sample.epub"

        metadata_parts = []

        if title is not None:
            metadata_parts.append(f"<dc:title>{title}</dc:title>")

        if author is not None:
            metadata_parts.append(f"<dc:creator>{author}</dc:creator>")

        with ZipFile(epub_path, "w") as archive:
            archive.writestr(
                "META-INF/container.xml",
                """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
""",
            )
            archive.writestr(
                "OEBPS/content.opf",
                f"""<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <metadata>
    {''.join(metadata_parts)}
  </metadata>
</package>
""",
            )

        return epub_path


if __name__ == "__main__":
    unittest.main()
