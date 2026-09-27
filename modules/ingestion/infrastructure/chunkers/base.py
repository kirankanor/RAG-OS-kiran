from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.registry import Registry
from shared.domain.types import Chunk, Document


class Chunker(ABC):
    name: str = "base"

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        raise NotImplementedError

    def _make_chunk(self, document, text, position, char_start, char_end) -> Chunk:
        return Chunk(document_id=document.id, text=text, position=position,
                      char_start=char_start, char_end=char_end, chunker_name=self.name)


chunker_registry: Registry[Chunker] = Registry("chunker")
