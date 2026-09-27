from __future__ import annotations

import re

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry

_DEF_RE = re.compile(
    r"^(?:\s*)(def |class |function |const \w+\s*=\s*\(|async def |public |private |static )",
    re.MULTILINE,
)


@chunker_registry.register("code_aware", "Splits source code on function/class definition boundaries.")
class CodeAwareChunker(Chunker):
    name = "code_aware"

    def __init__(self, max_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size

    def chunk(self, document):
        text = document.text
        matches = list(_DEF_RE.finditer(text))
        units = []
        if not matches:
            units.append((0, len(text), text))
        else:
            if matches[0].start() > 0:
                units.append((0, matches[0].start(), text[:matches[0].start()]))
            for idx, m in enumerate(matches):
                start = m.start()
                end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
                units.append((start, end, text[start:end]))
        chunks, position = [], 0
        for start, end, unit_text in units:
            if not unit_text.strip():
                continue
            if len(unit_text) <= self.max_chunk_size:
                chunks.append(self._make_chunk(document, unit_text, position, start, end))
                position += 1
                continue
            offset = 0
            while offset < len(unit_text):
                sub = unit_text[offset:offset + self.max_chunk_size]
                sub_start = start + offset
                sub_end = sub_start + len(sub)
                chunks.append(self._make_chunk(document, sub, position, sub_start, sub_end))
                position += 1
                offset += self.max_chunk_size
        return chunks
