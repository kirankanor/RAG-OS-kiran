from __future__ import annotations

from typing import Any

from modules.experiments.domain.interfaces.experiment_runner import (
    ExperimentRunner, experiment_runner_registry,
)
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.experiments.infrastructure.runners.ingestion_runner import build_pipeline
from modules.strategies.domain.entities.strategy import Strategy
from shared.ai.embeddings import embedder_registry


def resolve_top_k(config: ExperimentConfig, strategy: Strategy) -> int:
    return config.top_k or strategy.retrieval.top_k


def retrieve_for_queries(run_config, retriever, reranker, queries, top_k):
    """Same retrieve(+rerank) logic as the Streamlit Retrieval page. Returns {query: [RetrievalResult]}."""
    embedder = embedder_registry.create(run_config.embedder_name, **run_config.embedder_params)
    out = {}
    for q in queries:
        qv = embedder.embed_query(q)
        results = retriever.retrieve(qv, top_k=top_k * 3 if reranker else top_k, query_text=q)
        if reranker:
            results = reranker.rerank(q, results, top_k=top_k)
        out[q] = results[:top_k]
    return out


def summarize(results) -> list[dict[str, Any]]:
    return [{"chunk_id": r.chunk_id, "rank": r.rank, "score": float(r.score), "text": r.text[:200]}
            for r in results]


@experiment_runner_registry.register("retrieval", "Build the pipeline, then run the experiment's queries.")
class RetrievalRunner(ExperimentRunner):
    name = "retrieval"
    requires_queries = True

    def run(self, config: ExperimentConfig, strategy: Strategy) -> dict[str, Any]:
        run_config, documents, chunks, retriever, reranker = build_pipeline(config, strategy)
        top_k = resolve_top_k(config, strategy)
        by_query = retrieve_for_queries(run_config, retriever, reranker, config.queries, top_k)
        return {"pipeline_run_id": run_config.id, "num_documents": len(documents),
                "num_chunks": len(chunks), "top_k": top_k,
                "queries": {q: summarize(rs) for q, rs in by_query.items()}}