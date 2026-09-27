from __future__ import annotations
from shared.retrieval.pipeline_context import PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


@pipeline_step_registry.register("mmr", "Maximal Marginal Relevance reranking for diversity.")
class MmrReranker(PipelineStep):
    name = "mmr"
    category = "reranker"

    def __init__(self, lambda_mult: float = 0.5):
        self.lambda_mult = lambda_mult

    def run(self, ctx):
        pool = [c for c in ctx.candidates if c.vector is not None]
        if not pool:
            return ctx
        max_score = max(c.score for c in pool) or 1.0
        relevance = {id(c): c.score / max_score for c in pool}
        selected, remaining = [], list(pool)
        while remaining and len(selected) < ctx.top_k:
            best_candidate, best_mmr = None, float("-inf")
            for c in remaining:
                max_sim = max((_cosine(c.vector, s.vector) for s in selected), default=0.0)
                mmr = self.lambda_mult * relevance[id(c)] - (1 - self.lambda_mult) * max_sim
                if mmr > best_mmr:
                    best_mmr, best_candidate = mmr, c
            selected.append(best_candidate)
            remaining.remove(best_candidate)
        ctx.candidates = selected
        return ctx
