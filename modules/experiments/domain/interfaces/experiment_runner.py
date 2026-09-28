from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.strategies.domain.entities.strategy import Strategy
from shared.domain.registry import Registry


class ExperimentRunner(ABC):
    """Port: executes one strategy against an experiment's config and returns a
    JSON-serializable result dict. Should include 'pipeline_run_id' if a pipeline run was created."""

    name: str = "base"
    requires_queries: bool = False
    requires_generator: bool = False

    @abstractmethod
    def run(self, config: ExperimentConfig, strategy: Strategy) -> dict[str, Any]:
        raise NotImplementedError


experiment_runner_registry: Registry[ExperimentRunner] = Registry("experiment_runner")