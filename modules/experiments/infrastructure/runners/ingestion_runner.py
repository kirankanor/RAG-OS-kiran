from __future__ import annotations

from typing import Any

from modules.experiments.domain.interfaces.experiment_runner import (
    ExperimentRunner, experiment_runner_registry,
)
from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.experiments.infrastructure.pipeline_orchestration import run_dataset_generation
from modules.strategies.domain.entities.strategy import Strategy


def build_pipeline(config: ExperimentConfig, strategy: Strategy):
    """parse -> chunk -> embed -> index via the legacy pipeline (persists a RunRow).
    Returns (run_config, documents, chunks, retriever, reranker)."""
    run_config = strategy.to_run_config()
    _, documents, chunks, retriever, reranker = run_dataset_generation(config.file_paths, run_config)
    return run_config, documents, chunks, retriever, reranker


@experiment_runner_registry.register("ingestion", "Parse, chunk, embed and index only (no queries).")
class IngestionRunner(ExperimentRunner):
    name = "ingestion"

    def run(self, config: ExperimentConfig, strategy: Strategy) -> dict[str, Any]:
        run_config, documents, chunks, _, _ = build_pipeline(config, strategy)
        return {"pipeline_run_id": run_config.id, "num_documents": len(documents),
                "num_chunks": len(chunks)}