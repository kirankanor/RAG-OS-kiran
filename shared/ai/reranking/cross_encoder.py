from __future__ import annotations
from shared.domain.types import RetrievalResult
from shared.ai.reranking.base import Reranker, reranker_registry


@reranker_registry.register("cross_encoder", "Local cross-encoder reranker. Requires 'local' extra.")
class CrossEncoderReranker(Reranker):
    name = "cross_encoder"

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from sentence_transformers import CrossEncoder
        self.model_name = model_name
        self._model = CrossEncoder(model_name)

    def rerank(self, query, results, top_k=5):
        if not results:
            return results
        pairs = [(query, r.text) for r in results]
        scores = self._model.predict(pairs)
        reranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for rank, (r, score) in enumerate(reranked):
            out.append(RetrievalResult(chunk_id=r.chunk_id, score=float(score), rank=rank, text=r.text, metadata=r.metadata))
        return out
