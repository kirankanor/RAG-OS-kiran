"""LEGACY - kept unchanged for old runs."""
from __future__ import annotations
from abc import ABC, abstractmethod
from shared.domain.registry import Registry
from shared.domain.types import Chunk, RetrievalResult


class Retriever(ABC):
    name: str = "base"

    @abstractmethod
    def build(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        raise NotImplementedError

    @abstractmethod
    def retrieve(self, query_vector, top_k: int = 5, query_text: str = "") -> list[RetrievalResult]:
        raise NotImplementedError


retriever_registry: Registry[Retriever] = Registry("retriever")
