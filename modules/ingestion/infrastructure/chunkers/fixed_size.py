from __future__ import annotations

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry


@chunker_registry.register("fixed_size", "Splits text into fixed-size character windows with overlap.")
class FixedSizeChunker(Chunker):
    name = "fixed_size"

    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document):
        text = document.text
        step = max(1, self.chunk_size - self.overlap)
        chunks, position, start = [], 0, 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            piece = text[start:end]
            if piece.strip():
                chunks.append(self._make_chunk(document, piece, position, start, end))
                position += 1
            if end == len(text):
                break
            start += step
        return chunks
