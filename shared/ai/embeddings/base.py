from __future__ import annotations
from abc import ABC, abstractmethod
from shared.domain.registry import Registry


class Embedder(ABC):
    name: str = "base"
    dim: int = 0

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]


embedder_registry: Registry[Embedder] = Registry("embedder")
