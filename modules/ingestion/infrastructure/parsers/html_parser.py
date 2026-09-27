from __future__ import annotations

from pathlib import Path

from shared.domain.types import Document
from modules.ingestion.infrastructure.parsers.base import Parser, parser_registry


@parser_registry.register("html_bs4", "Strips tags/scripts/styles from HTML using BeautifulSoup.")
class Bs4HtmlParser(Parser):
    name = "html_bs4"

    @classmethod
    def supported_extensions(cls) -> tuple[str, ...]:
        return (".html", ".htm")

    def parse(self, file_path):
        from bs4 import BeautifulSoup
        path = Path(file_path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        text = "\n".join(line for line in lines if line)
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        return Document(source_filename=path.name, text=text, parser_name=self.name,
                         metadata={"title": title, "num_chars": len(text)})
