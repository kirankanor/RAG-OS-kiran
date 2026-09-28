from __future__ import annotations

from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment import Experiment


class StopExperimentCommand:
    def __init__(self, service: ExperimentService | None = None):
        self.service = service or ExperimentService()

    def execute(self, experiment_id: str) -> Experiment:
        return self.service.stop(experiment_id)