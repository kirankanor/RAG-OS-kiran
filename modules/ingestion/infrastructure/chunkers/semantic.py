from __future__ import annotations

import re
from collections.abc import Callable

from modules.ingestion.infrastructure.chunkers.base import Chunker, chunker_registry

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
EmbedFn = Callable[[list], list]


@chunker_registry.register("semantic", "Splits sentences, starts new chunk where topic shifts.")
class SemanticChunker(Chunker):
    name = "semantic"

    def __init__(self, embed_fn=None, similarity_threshold: float = 0.65, max_chunk_size: int = 2000):
        self.embed_fn = embed_fn
        self.similarity_threshold = similarity_threshold
        self.max_chunk_size = max_chunk_size

    @staticmethod
    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb) if na and nb else 0.0

    def chunk(self, document):
        if self.embed_fn is None:
            raise ValueError("SemanticChunker requires an embed_fn.")
        text = document.text
        sentences = [s for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
        if not sentences:
            return []
        if len(sentences) == 1:
            return [self._make_chunk(document, sentences[0], 0, 0, len(sentences[0]))]
        vectors = self.embed_fn(sentences)
        groups = [[sentences[0]]]
        for i in range(1, len(sentences)):
            sim = self._cosine(vectors[i - 1], vectors[i])
            current_len = sum(len(s) for s in groups[-1])
            if sim >= self.similarity_threshold and current_len < self.max_chunk_size:
                groups[-1].append(sentences[i])
            else:
                groups.append([sentences[i]])
        chunks, cursor = [], 0
        for position, group in enumerate(groups):
            piece = " ".join(group)
            start = text.find(group[0][:30], cursor) if group[0] else cursor
            start = max(start, 0)
            end = start + len(piece)
            chunks.append(self._make_chunk(document, piece, position, start, end))
            cursor = start
        return chunks
