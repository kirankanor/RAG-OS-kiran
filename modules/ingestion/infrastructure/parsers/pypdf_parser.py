from __future__ import annotations

from pathlib import Path

from shared.domain.types import Document
from modules.ingestion.infrastructure.parsers.base import Parser, parser_registry


@parser_registry.register("pdf_pypdf", "Extracts text from PDFs using pypdf.")
class PyPdfParser(Parser):
    name = "pdf_pypdf"

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".pdf",)

    def parse(self, file_path):
        from pypdf import PdfReader
        path = Path(file_path)
        reader = PdfReader(str(path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(text_parts)
        return Document(source_filename=path.name, text=text, parser_name=self.name,
                         metadata={"num_pages": len(reader.pages), "num_chars": len(text)})
