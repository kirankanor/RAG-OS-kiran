from __future__ import annotations

from typing import Any

from modules.experiments.domain.interfaces.experiment_runner import (
    ExperimentRunner, experiment_runner_registry,
)
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.experiments.infrastructure.runners.ingestion_runner import build_pipeline
from modules.experiments.infrastructure.runners.retrieval_runner import (
    resolve_top_k, retrieve_for_queries, summarize,
)
from modules.strategies.domain.entities.strategy import Strategy
from shared.ai.llm import generator_registry


@experiment_runner_registry.register("rag", "Retrieval plus answer generation per query.")
class RagRunner(ExperimentRunner):
    name = "rag"
    requires_queries = True
    requires_generator = True

    def run(self, config: ExperimentConfig, strategy: Strategy) -> dict[str, Any]:
        generator = generator_registry.create(config.generator_name, **config.generator_params)
        run_config, documents, chunks, retriever, reranker = build_pipeline(config, strategy)
        top_k = resolve_top_k(config, strategy)
        by_query = retrieve_for_queries(run_config, retriever, reranker, config.queries, top_k)
        return {"pipeline_run_id": run_config.id, "num_documents": len(documents),
                "num_chunks": len(chunks), "top_k": top_k,
                "queries": {q: summarize(rs) for q, rs in by_query.items()},
                "answers": {q: generator.generate(q, rs) for q, rs in by_query.items()}}