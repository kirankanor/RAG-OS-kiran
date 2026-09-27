from __future__ import annotations

import re

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@chunker_registry.register("sentence_window", "Groups N sentences per chunk with overlap.")
class SentenceWindowChunker(Chunker):
    name = "sentence_window"

    def __init__(self, sentences_per_chunk: int = 5, sentence_overlap: int = 1):
        self.sentences_per_chunk = max(1, sentences_per_chunk)
        self.sentence_overlap = max(0, min(sentence_overlap, sentences_per_chunk - 1))

    def chunk(self, document):
        text = document.text
        sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
        if not sentences:
            return []
        step = self.sentences_per_chunk - self.sentence_overlap
        chunks, position, i, cursor = [], 0, 0, 0
        while i < len(sentences):
            window = sentences[i:i + self.sentences_per_chunk]
            piece = " ".join(window)
            start = text.find(window[0][:30], cursor) if window[0] else cursor
            start = max(start, 0)
            end = start + len(piece)
            chunks.append(self._make_chunk(document, piece, position, start, end))
            cursor = start
            position += 1
            i += step
        return chunks
