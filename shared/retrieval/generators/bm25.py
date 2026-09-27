from __future__ import annotations
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


@pipeline_step_registry.register("bm25", "Lexical BM25 search. Requires 'local' extra (rank-bm25).")
class Bm25Generator(PipelineStep):
    name = "bm25"
    category = "generator"

    def __init__(self, fetch_k: int = 20):
        self.fetch_k = fetch_k

    def run(self, ctx):
        from rank_bm25 import BM25Okapi
        if not ctx.all_chunks or not ctx.query.strip():
            return ctx
        tokenized_corpus = [c.text.lower().split() for c in ctx.all_chunks]
        bm25 = BM25Okapi(tokenized_corpus)
        scores = bm25.get_scores(ctx.query.lower().split())
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        k = min(self.fetch_k, len(ctx.all_chunks))
        for idx, score in ranked[:k]:
            chunk = ctx.all_chunks[idx]
            ctx.candidates.append(Candidate(chunk=chunk, vector=ctx.all_vectors.get(chunk.id), score=float(score), source_step=self.name))
        return ctx
