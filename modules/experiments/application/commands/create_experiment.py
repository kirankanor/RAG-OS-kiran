from __future__ import annotations

from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment import Experiment
from modules.experiments.domain.models.experiment_config import ExperimentConfig, StrategyRef


class CreateExperimentCommand:
    def __init__(self, service: ExperimentService | None = None):
        self.service = service or ExperimentService()

    def execute(self, name: str, config: ExperimentConfig, strategy_refs: list[StrategyRef | str],
                description: str = "") -> Experiment:
        return self.service.create(name, config, strategy_refs, description)