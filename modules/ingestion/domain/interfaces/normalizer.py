from __future__ import annotations

from abc import ABC, abstractmethod

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from shared.domain.registry import Registry


class Normalizer(ABC):
    """Port for a normalization stage: cleans up/standardizes a
    CanonicalDocument's text/structure (e.g. whitespace, encoding, heading
    hierarchy) before chunking."""

    name: str = "base"

    @abstractmethod
    def normalize(self, document: CanonicalDocument) -> CanonicalDocument:
        raise NotImplementedError


normalizer_registry: Registry[Normalizer] = Registry("normalizer")
