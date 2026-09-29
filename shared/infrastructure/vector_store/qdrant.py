from __future__ import annotations

from shared.config.settings import get_settings
from shared.infrastructure.vector_store.base import (
    VectorMatch, VectorRecord, VectorStore, vector_store_registry,
)


@vector_store_registry.register("qdrant", "Qdrant-backed VectorStore. Requires 'cloud' extra + running Qdrant.")
class QdrantVectorStore(VectorStore):
    """Thin client wrapper, independent of the retrieval pipeline (see
    shared.retrieval.generators.qdrant_dense for the PipelineStep that currently
    talks to Qdrant directly instead of through this port)."""

    name = "qdrant"

    def __init__(self, url: str | None = None, api_key: str | None = None):
        from qdrant_client import QdrantClient
        settings = get_settings()
        self._client = QdrantClient(url=url or settings.qdrant_url, api_key=api_key or settings.qdrant_api_key)

    def ensure_collection(self, collection_name: str, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams
        self._client.recreate_collection(collection_name=collection_name,
                                          vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

    def upsert(self, collection_name: str, records: list[VectorRecord]) -> None:
        from qdrant_client.models import PointStruct
        points = [PointStruct(id=r.id, vector=r.vector, payload=r.payload) for r in records]
        if points:
            self._client.upsert(collection_name=collection_name, points=points)

    def search(self, collection_name: str, query_vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        hits = self._client.search(collection_name=collection_name, query_vector=query_vector, limit=top_k)
        return [VectorMatch(id=str(h.id), score=float(h.score), payload=h.payload or {}) for h in hits]

    def delete_collection(self, collection_name: str) -> None:
        self._client.delete_collection(collection_name=collection_name)
