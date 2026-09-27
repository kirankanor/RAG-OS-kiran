from __future__ import annotations
from abc import ABC, abstractmethod
from shared.domain.registry import Registry
from shared.domain.types import RetrievalResult


class Reranker(ABC):
    name: str = "base"

    @abstractmethod
    def rerank(self, query: str, results: list[RetrievalResult], top_k: int = 5) -> list[RetrievalResult]:
        raise NotImplementedError


reranker_registry: Registry[Reranker] = Registry("reranker")
