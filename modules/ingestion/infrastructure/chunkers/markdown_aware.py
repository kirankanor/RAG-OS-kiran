from __future__ import annotations

import re

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)


@chunker_registry.register("markdown_aware", "Splits on Markdown headings, then size-based sub-splits.")
class MarkdownAwareChunker(Chunker):
    name = "markdown_aware"

    def __init__(self, max_chunk_size: int = 1200):
        self.max_chunk_size = max_chunk_size

    def chunk(self, document):
        text = document.text
        matches = list(_HEADING_RE.finditer(text))
        sections = []
        if not matches:
            sections.append((0, len(text), text))
        else:
            for idx, m in enumerate(matches):
                start = m.start()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                sections.append((start, end, text[start:end]))
        chunks, position = [], 0
        for start, end, section_text in sections:
            if len(section_text) <= self.max_chunk_size:
                chunks.append(self._make_chunk(document, section_text, position, start, end))
                position += 1
                continue
            offset = 0
            while offset < len(section_text):
                sub = section_text[offset:offset + self.max_chunk_size]
                sub_start = start + offset
                sub_end = sub_start + len(sub)
                chunks.append(self._make_chunk(document, sub, position, sub_start, sub_end))
                position += 1
                offset += self.max_chunk_size
        return chunks
