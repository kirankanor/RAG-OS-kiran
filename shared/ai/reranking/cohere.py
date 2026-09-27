from __future__ import annotations
import os
from shared.domain.types import RetrievalResult
from shared.ai.reranking.base import Reranker, reranker_registry


@reranker_registry.register("cohere_rerank", "Cohere rerank API. Requires COHERE_API_KEY.")
class CohereReranker(Reranker):
    name = "cohere_rerank"

    def __init__(self, model: str = "rerank-english-v3.0", api_key: str | None = None):
        import cohere
        key = api_key or os.environ.get("COHERE_API_KEY")
        if not key:
            raise ValueError("No Cohere API key found.")
        self.model = model
        self._client = cohere.Client(key)

    def rerank(self, query, results, top_k=5):
        if not results:
            return results
        response = self._client.rerank(query=query, documents=[r.text for r in results], top_n=top_k, model=self.model)
        out = []
        for rank, item in enumerate(response.results):
            r = results[item.index]
            out.append(RetrievalResult(chunk_id=r.chunk_id, score=float(item.relevance_score), rank=rank, text=r.text, metadata=r.metadata))
        return out
