"""LEGACY - kept for old runs. New pipelines use generators/qdrant_dense.py."""
from __future__ import annotations
import uuid
from shared.domain.types import RetrievalResult
from shared.retrieval.legacy_base import Retriever, retriever_registry


@retriever_registry.register("qdrant", "Vector search via Qdrant. Requires 'cloud' extra + running Qdrant instance.")
class QdrantRetriever(Retriever):
    name = "qdrant"

    def __init__(self, collection_name: str = "rag_os_experiment", url: str = "http://localhost:6333", api_key=None):
        from qdrant_client import QdrantClient
        self.collection_name = collection_name
        self._client = QdrantClient(url=url, api_key=api_key)
        self._id_map = {}

    def build(self, chunks, vectors):
        from qdrant_client.models import Distance, PointStruct, VectorParams
        dim = len(vectors[0]) if vectors else 0
        self._client.recreate_collection(collection_name=self.collection_name,
                                          vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
        points = []
        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid.uuid4())
            self._id_map[point_id] = chunk
            points.append(PointStruct(id=point_id, vector=vector, payload={"chunk_id": chunk.id}))
        self._client.upsert(collection_name=self.collection_name, points=points)

    def retrieve(self, query_vector, top_k=5, query_text=""):
        hits = self._client.search(collection_name=self.collection_name, query_vector=query_vector, limit=top_k)
        results = []
        for rank, hit in enumerate(hits):
            chunk = self._id_map.get(str(hit.id))
            if chunk is None:
                continue
            results.append(RetrievalResult(chunk_id=chunk.id, score=float(hit.score), rank=rank, text=chunk.text, metadata=chunk.metadata))
        return results
