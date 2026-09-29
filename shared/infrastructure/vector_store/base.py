from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from shared.domain.registry import Registry


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorMatch:
    id: str
    score: float
    payload: dict[str, Any] = field(default_factory=dict)


class VectorStore(ABC):
    """Port for a vector database backend: create/reset a collection, upsert vectors,
    search by similarity. Distinct from shared.retrieval.generators.qdrant_dense, which
    is one PipelineStep implementation coupled to the retrieval pipeline's Candidate/
    PipelineContext shape -- this is the lower-level client abstraction it could sit on."""

    name: str = "base"

    @abstractmethod
    def ensure_collection(self, collection_name: str, dim: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def search(self, collection_name: str, query_vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        raise NotImplementedError


vector_store_registry: Registry[VectorStore] = Registry("vector_store")
