from __future__ import annotations
import uuid
from shared.retrieval.pipeline_context import Candidate, PipelineContext
from shared.retrieval.pipeline_step import PipelineStep, pipeline_step_registry


@pipeline_step_registry.register("qdrant_dense", "Dense vector search via Qdrant. Requires 'cloud' extra + running Qdrant.")
class QdrantDenseGenerator(PipelineStep):
    name = "qdrant_dense"
    category = "generator"

    def __init__(self, fetch_k: int = 20, collection_name: str = "rag_os_experiment",
                 url: str = "http://localhost:6333", api_key=None):
        self.fetch_k = fetch_k
        self.collection_name = collection_name
        self.url = url
        self.api_key = api_key

    def run(self, ctx):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
        if ctx.query_vector is None or not ctx.all_chunks:
            return ctx
        client = QdrantClient(url=self.url, api_key=self.api_key)
        dim = len(ctx.query_vector)
        client.recreate_collection(collection_name=self.collection_name,
                                    vectors_config=VectorParams(size=dim, distance=Distance.COSINE))
        id_map = {}
        points = []
        for chunk in ctx.all_chunks:
            vector = ctx.all_vectors.get(chunk.id)
            if vector is None:
                continue
            point_id = str(uuid.uuid4())
            id_map[point_id] = chunk.id
            points.append(PointStruct(id=point_id, vector=vector, payload={"chunk_id": chunk.id}))
        if points:
            client.upsert(collection_name=self.collection_name, points=points)
        k = min(self.fetch_k, len(ctx.all_chunks))
        hits = client.search(collection_name=self.collection_name, query_vector=ctx.query_vector, limit=k)
        chunks_by_id = ctx.chunks_by_id()
        for hit in hits:
            chunk_id = id_map.get(str(hit.id))
            if chunk_id is None:
                continue
            chunk = chunks_by_id.get(chunk_id)
            if chunk is None:
                continue
            ctx.candidates.append(Candidate(chunk=chunk, vector=ctx.all_vectors.get(chunk_id), score=float(hit.score), source_step=self.name))
        return ctx
