"""LEGACY - kept for old runs. New pipelines use generators/dense_vector.py."""
from __future__ import annotations
from shared.domain.types import RetrievalResult
from shared.retrieval.legacy_base import Retriever, retriever_registry


@retriever_registry.register("faiss_flat_l2", "Exact FAISS IndexFlatL2 search. Requires 'local' extra.")
class FaissFlatRetriever(Retriever):
    name = "faiss_flat_l2"

    def __init__(self):
        self._index = None
        self._chunks = []

    def build(self, chunks, vectors):
        import faiss, numpy as np
        self._chunks = chunks
        matrix = np.array(vectors, dtype="float32")
        self._index = faiss.IndexFlatL2(matrix.shape[1])
        self._index.add(matrix)

    def retrieve(self, query_vector, top_k=5, query_text=""):
        import numpy as np
        if self._index is None:
            raise RuntimeError("Call build() before retrieve().")
        query = np.array([query_vector], dtype="float32")
        distances, indices = self._index.search(query, top_k)
        results = []
        for rank, (idx, dist) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:
                continue
            chunk = self._chunks[idx]
            score = 1.0 / (1.0 + float(dist))
            results.append(RetrievalResult(chunk_id=chunk.id, score=score, rank=rank, text=chunk.text, metadata=chunk.metadata))
        return results
