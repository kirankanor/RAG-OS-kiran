"""Thin PipelineStep wrappers around the legacy Reranker classes in this package."""
from __future__ import annotations
from shared.domain.types import RetrievalResult
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


def _candidates_to_results(candidates):
    return [RetrievalResult(chunk_id=c.chunk.id, score=c.score, rank=i, text=c.chunk.text, metadata=c.chunk.metadata)
            for i, c in enumerate(candidates)]


def _reorder_candidates(candidates, reranked_results):
    by_chunk_id = {c.chunk.id: c for c in candidates}
    ordered = []
    for r in reranked_results:
        c = by_chunk_id.get(r.chunk_id)
        if c is not None:
            c.score = r.score
            ordered.append(c)
    return ordered


@pipeline_step_registry.register("cross_encoder_rerank", "Pipeline-step wrapper around rerankers.cross_encoder.")
class CrossEncoderRerankStep(PipelineStep):
    name = "cross_encoder_rerank"
    category = "reranker"

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        from shared.ai.reranking.cross_encoder import CrossEncoderReranker
        self._reranker = CrossEncoderReranker(model_name=model_name)

    def run(self, ctx):
        if not ctx.candidates:
            return ctx
        results = _candidates_to_results(ctx.candidates)
        reranked = self._reranker.rerank(ctx.query, results, top_k=ctx.top_k)
        ctx.candidates = _reorder_candidates(ctx.candidates, reranked)
        return ctx


@pipeline_step_registry.register("cohere_rerank", "Pipeline-step wrapper around rerankers.cohere_rerank.")
class CohereRerankStep(PipelineStep):
    name = "cohere_rerank"
    category = "reranker"

    def __init__(self, model: str = "rerank-english-v3.0", api_key: str | None = None):
        from shared.ai.reranking.cohere import CohereReranker
        self._reranker = CohereReranker(model=model, api_key=api_key)

    def run(self, ctx):
        if not ctx.candidates:
            return ctx
        results = _candidates_to_results(ctx.candidates)
        reranked = self._reranker.rerank(ctx.query, results, top_k=ctx.top_k)
        ctx.candidates = _reorder_candidates(ctx.candidates, reranked)
        return ctx
