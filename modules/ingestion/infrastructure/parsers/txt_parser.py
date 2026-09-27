from __future__ import annotations

from pathlib import Path

from shared.domain.types import Document
from modules.ingestion.infrastructure.parsers.base import Parser, parser_registry


@parser_registry.register("txt_plain", "Reads a .txt/.md file as-is.")
class PlainTextParser(Parser):
    name = "txt_plain"

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".txt", ".md")

    def parse(self, file_path):
        path = Path(file_path)
        text = path.read_text(encoding="utf-8", errors="replace")
        return Document(source_filename=path.name, text=text, parser_name=self.name,
                         metadata={"num_chars": len(text)})
