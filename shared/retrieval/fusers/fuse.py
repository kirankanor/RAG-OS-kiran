from __future__ import annotations
from collections import defaultdict
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


def _group_by_chunk(candidates):
    groups = defaultdict(list)
    for c in candidates:
        groups[c.chunk.id].append(c)
    return groups


@pipeline_step_registry.register("rrf_fuse", "Reciprocal Rank Fusion across multiple generators.")
class RrfFuser(PipelineStep):
    name = "rrf_fuse"
    category = "fuser"

    def __init__(self, k: int = 60):
        self.k = k

    def run(self, ctx):
        groups = _group_by_chunk(ctx.candidates)
        if not groups:
            return ctx
        by_source = defaultdict(list)
        for c in ctx.candidates:
            by_source[c.source_step].append(c)
        for source_candidates in by_source.values():
            source_candidates.sort(key=lambda c: c.score, reverse=True)
        rrf_scores = defaultdict(float)
        for source_candidates in by_source.values():
            for rank, c in enumerate(source_candidates):
                rrf_scores[c.chunk.id] += 1.0 / (self.k + rank + 1)
        fused = []
        for chunk_id, group in groups.items():
            best = group[0]
            fused.append(Candidate(chunk=best.chunk, vector=best.vector, score=rrf_scores[chunk_id],
                                    source_step=self.name, parent_text=best.parent_text))
        fused.sort(key=lambda c: c.score, reverse=True)
        ctx.candidates = fused
        return ctx


@pipeline_step_registry.register("weighted_fuse", "Min-max normalize + weighted blend across generators.")
class WeightedFuser(PipelineStep):
    name = "weighted_fuse"
    category = "fuser"

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or {}

    @staticmethod
    def _normalize(scores):
        if not scores:
            return scores
        lo, hi = min(scores), max(scores)
        if hi - lo < 1e-9:
            return [0.0 for _ in scores]
        return [(s - lo) / (hi - lo) for s in scores]

    def run(self, ctx):
        by_source = defaultdict(list)
        for c in ctx.candidates:
            by_source[c.source_step].append(c)
        if not by_source:
            return ctx
        default_weight = 1.0 / len(by_source)
        normalized_scores = {}
        for source, cands in by_source.items():
            norm = self._normalize([c.score for c in cands])
            normalized_scores[source] = {c.chunk.id: n for c, n in zip(cands, norm)}
        combined = defaultdict(float)
        chunk_lookup = {}
        for source, cands in by_source.items():
            weight = self.weights.get(source, default_weight)
            for c in cands:
                combined[c.chunk.id] += weight * normalized_scores[source][c.chunk.id]
                chunk_lookup[c.chunk.id] = c
        fused = []
        for chunk_id, score in combined.items():
            base = chunk_lookup[chunk_id]
            fused.append(Candidate(chunk=base.chunk, vector=base.vector, score=score,
                                    source_step=self.name, parent_text=base.parent_text))
        fused.sort(key=lambda c: c.score, reverse=True)
        ctx.candidates = fused
        return ctx
