from pathlib import Path

from pypdf import PdfReader

from book_indexer.parsers.base import ParseResult

TEXT_LIMIT = 15000


class PDFParser:
    def parse(self, path: Path) -> ParseResult:
        try:
            reader = PdfReader(path)

            parts = []

            for page in reader.pages[:10]:
                text = page.extract_text()
                if not text:
                    continue

                text = text.strip()
                if len(text) < 50:
                    continue

                parts.append(text)

            full_text = "\n".join(parts).strip()

            if len(full_text) > TEXT_LIMIT:
                full_text = full_text[:TEXT_LIMIT]

            return ParseResult(
                title=path.stem,
                author=None,
                text=full_text if full_text else None,
                status="ok" if full_text else "partial",
            )
        except Exception as e:
            return ParseResult(
                title=path.stem,
                author=None,
                text=None,
                status="failed",
                error=str(e),
            )
