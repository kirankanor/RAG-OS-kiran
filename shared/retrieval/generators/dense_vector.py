from __future__ import annotations
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


@pipeline_step_registry.register("dense_flat", "Exact dense vector search via FAISS IndexFlatL2.")
class DenseFlatGenerator(PipelineStep):
    name = "dense_flat"
    category = "generator"

    def __init__(self, fetch_k: int = 20):
        self.fetch_k = fetch_k

    def run(self, ctx):
        import faiss, numpy as np
        if ctx.query_vector is None or not ctx.all_chunks:
            return ctx
        chunk_ids = [c.id for c in ctx.all_chunks]
        matrix = np.array([ctx.all_vectors[cid] for cid in chunk_ids], dtype="float32")
        index = faiss.IndexFlatL2(matrix.shape[1])
        index.add(matrix)
        query = np.array([ctx.query_vector], dtype="float32")
        k = min(self.fetch_k, len(chunk_ids))
        distances, indices = index.search(query, k)
        chunks_by_id = ctx.chunks_by_id()
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            cid = chunk_ids[idx]
            chunk = chunks_by_id[cid]
            score = 1.0 / (1.0 + float(dist))
            ctx.candidates.append(Candidate(chunk=chunk, vector=ctx.all_vectors.get(cid), score=score, source_step=self.name))
        return ctx


@pipeline_step_registry.register("dense_hnsw", "Approximate dense vector search via FAISS IndexHNSWFlat.")
class DenseHnswGenerator(PipelineStep):
    name = "dense_hnsw"
    category = "generator"

    def __init__(self, fetch_k: int = 20, m: int = 32, ef_search: int = 64):
        self.fetch_k = fetch_k
        self.m = m
        self.ef_search = ef_search

    def run(self, ctx):
        import faiss, numpy as np
        if ctx.query_vector is None or not ctx.all_chunks:
            return ctx
        chunk_ids = [c.id for c in ctx.all_chunks]
        matrix = np.array([ctx.all_vectors[cid] for cid in chunk_ids], dtype="float32")
        index = faiss.IndexHNSWFlat(matrix.shape[1], self.m)
        index.hnsw.efSearch = self.ef_search
        index.add(matrix)
        query = np.array([ctx.query_vector], dtype="float32")
        k = min(self.fetch_k, len(chunk_ids))
        distances, indices = index.search(query, k)
        chunks_by_id = ctx.chunks_by_id()
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            cid = chunk_ids[idx]
            chunk = chunks_by_id[cid]
            score = 1.0 / (1.0 + float(dist))
            ctx.candidates.append(Candidate(chunk=chunk, vector=ctx.all_vectors.get(cid), score=score, source_step=self.name))
        return ctx
