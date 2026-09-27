"""LEGACY - unchanged (includes RRF fusion_method), kept for old runs."""
from __future__ import annotations
from shared.domain.types import RetrievalResult
from shared.retrieval.legacy_base import Retriever, retriever_registry


@retriever_registry.register("hybrid_bm25_vector", "BM25 + dense vector weighted/RRF fusion. Requires 'local' extra.")
class HybridBm25VectorRetriever(Retriever):
    name = "hybrid_bm25_vector"

    def __init__(self, alpha: float = 0.5, fusion_method: str = "weighted", rrf_k: int = 60):
        self.alpha = alpha
        self.fusion_method = fusion_method
        self.rrf_k = rrf_k
        self._chunks = []
        self._vectors = []
        self._bm25 = None

    def build(self, chunks, vectors):
        from rank_bm25 import BM25Okapi
        self._chunks = chunks
        self._vectors = vectors
        tokenized = [c.text.lower().split() for c in chunks]
        self._bm25 = BM25Okapi(tokenized)

    @staticmethod
    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        return dot / (na * nb) if na and nb else 0.0

    @staticmethod
    def _normalize(scores):
        if not scores:
            return scores
        lo, hi = min(scores), max(scores)
        if hi - lo < 1e-9:
            return [0.0 for _ in scores]
        return [(s - lo) / (hi - lo) for s in scores]

    @staticmethod
    def _ranks(scores):
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        ranks = [0] * len(scores)
        for r, i in enumerate(order):
            ranks[i] = r
        return ranks

    def retrieve(self, query_vector, top_k=5, query_text=""):
        if self._bm25 is None:
            raise RuntimeError("Call build() before retrieve().")
        bm25_raw = list(self._bm25.get_scores(query_text.lower().split()))
        vector_raw = [self._cosine(query_vector, v) for v in self._vectors]
        if self.fusion_method == "rrf":
            bm25_ranks = self._ranks(bm25_raw)
            vector_ranks = self._ranks(vector_raw)
            combined = [1.0 / (self.rrf_k + bm25_ranks[i]) + 1.0 / (self.rrf_k + vector_ranks[i])
                        for i in range(len(self._chunks))]
        else:
            bm25_scores = self._normalize(bm25_raw)
            vector_scores = self._normalize(vector_raw)
            combined = [self.alpha * v + (1 - self.alpha) * b for v, b in zip(vector_scores, bm25_scores)]
        ranked = sorted(enumerate(combined), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for rank, (idx, score) in enumerate(ranked):
            chunk = self._chunks[idx]
            results.append(RetrievalResult(chunk_id=chunk.id, score=float(score), rank=rank, text=chunk.text, metadata=chunk.metadata))
        return results
