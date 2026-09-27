from __future__ import annotations

from pathlib import Path

from shared.domain.types import Document
from modules.ingestion.infrastructure.parsers.base import Parser, parser_registry


@parser_registry.register(
    "pdf_pymupdf",
    "Extracts text from PDFs using PyMuPDF (fitz). Requires the 'local' extra.",
)
class PyMuPdfParser(Parser):
    name = "pdf_pymupdf"

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".pdf",)

    def parse(self, file_path):
        import fitz
        path = Path(file_path)
        text_parts = []
        with fitz.open(path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
            num_pages = doc.page_count
        text = "\n\n".join(text_parts)
        return Document(source_filename=path.name, text=text, parser_name=self.name,
                         metadata={"num_pages": num_pages, "num_chars": len(text)})
