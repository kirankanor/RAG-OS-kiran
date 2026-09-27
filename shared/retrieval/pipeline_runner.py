from __future__ import annotations
from shared.domain.types import RetrievalResult
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import pipeline_step_registry
# Side-effect imports: importing these modules registers their pipeline steps /
# strategies into the shared registries. Split across shared.retrieval (expanders,
# filters, fusers, generators, mmr, reranker_pipeline_adapters) and shared.ai.reranking
# (cross_encoder, cohere) since the old rag_os.retrieval.rerankers package straddled
# both destinations after the restructure.
from shared.retrieval import expanders, filters, fusers, generators, mmr, reranker_pipeline_adapters  # noqa: F401
from shared.ai.reranking import cross_encoder, cohere  # noqa: F401


class PipelineStepConfig:
    def __init__(self, step_name: str, params: dict | None = None):
        self.step_name = step_name
        self.params = params or {}


def run_pipeline(step_configs, query, query_vector, all_chunks, all_vectors, top_k=5):
    ctx = PipelineContext(query=query, query_vector=query_vector, all_chunks=all_chunks,
                           all_vectors=all_vectors, top_k=top_k)
    for step_config in step_configs:
        step = pipeline_step_registry.create(step_config.step_name, **step_config.params)
        ctx = step.run(ctx)
    if len(ctx.candidates) > top_k:
        ctx.candidates = sorted(ctx.candidates, key=lambda c: c.score, reverse=True)[:top_k]
    return _candidates_to_results(ctx.candidates)


def _candidates_to_results(candidates):
    results = []
    for rank, c in enumerate(candidates):
        metadata = dict(c.chunk.metadata)
        if c.parent_text:
            metadata["expanded_context"] = c.parent_text
        results.append(RetrievalResult(chunk_id=c.chunk.id, score=c.score, rank=rank, text=c.chunk.text, metadata=metadata))
    return results
