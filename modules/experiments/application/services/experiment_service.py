from __future__ import annotations

from pathlib import Path

from sqlmodel import SQLModel

from modules.experiments.domain.entities.experiment import Experiment
from modules.experiments.domain.entities.experiment_run import ExperimentRun
from modules.experiments.domain.exceptions import ExperimentNotFoundError, InvalidExperimentError
from modules.experiments.domain.interfaces.experiment_runner import experiment_runner_registry
from modules.experiments.domain.models.experiment_config import ExperimentConfig, StrategyRef
from modules.experiments.infrastructure import runners as _runners  # noqa: F401  (registers runners)
from modules.experiments.infrastructure.persistence import models as _models  # noqa: F401
from modules.experiments.infrastructure.persistence.repository import ExperimentRepository
from modules.strategies.application.services.strategy_service import StrategyService
from shared.ai.llm import generator_registry
from shared.infrastructure.database.db_models import get_engine


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class ExperimentService:
    def __init__(self, repository: ExperimentRepository | None = None,
                 strategy_service: StrategyService | None = None):
        _ensure_tables()
        self.repository = repository or ExperimentRepository()
        self.strategies = strategy_service or StrategyService()

    def create(self, name: str, config: ExperimentConfig, strategy_refs: list[StrategyRef | str],
               description: str = "") -> Experiment:
        refs = [StrategyRef(r) if isinstance(r, str) else r for r in strategy_refs]
        errors: list[str] = []
        if not name.strip():
            errors.append("Experiment name is required.")
        if config.runner not in experiment_runner_registry.names():
            errors.append(f"Unknown runner '{config.runner}'. Available: {experiment_runner_registry.names()}")
        else:
            runner_cls = experiment_runner_registry.get(config.runner)
            if runner_cls.requires_queries and not any(q.strip() for q in config.queries):
                errors.append(f"Runner '{config.runner}' needs at least one query.")
            if runner_cls.requires_generator and config.generator_name not in generator_registry.names():
                errors.append(f"Runner '{config.runner}' needs a valid generator_name "
                              f"(available: {generator_registry.names()}).")
        if not config.file_paths:
            errors.append("At least one file path is required.")
        errors.extend(f"File not found: {fp}" for fp in config.file_paths if not Path(fp).is_file())
        if config.top_k is not None and config.top_k < 1:
            errors.append("top_k must be >= 1.")
        if not refs:
            errors.append("At least one strategy is required.")
        keys = [(r.strategy_id, r.version) for r in refs]
        if len(set(keys)) != len(keys):
            errors.append("Duplicate strategies.")
        if errors:
            raise InvalidExperimentError("Invalid experiment: " + "; ".join(errors), errors)

        pinned = [StrategyRef(r.strategy_id, self.strategies.get(r.strategy_id, r.version).version.number)
                  for r in refs]  # raises StrategyNotFoundError; pins "current" to a concrete version
        experiment = Experiment(name=name.strip(), description=description, config=config,
                                strategy_refs=pinned)
        experiment.runs = [ExperimentRun(experiment_id=str(experiment.id), position=i,
                                         strategy_id=r.strategy_id, strategy_version=r.version)
                           for i, r in enumerate(pinned)]
        self.repository.save(experiment)
        return experiment

    def get(self, experiment_id: str) -> Experiment:
        e = self.repository.get(experiment_id)
        if e is None:
            raise ExperimentNotFoundError(f"No experiment with id '{experiment_id}'")
        return e

    def list(self) -> list[Experiment]:
        return self.repository.list()

    def get_runs(self, experiment_id: str) -> list[ExperimentRun]:
        self.get(experiment_id)
        return self.repository.get_runs(experiment_id)

    def stop(self, experiment_id: str) -> Experiment:
        """Cooperative: pending runs are cancelled now; a run already executing finishes."""
        self.get(experiment_id)
        self.repository.mark_cancelled(experiment_id)
        return self.get(experiment_id)