from __future__ import annotations

from modules.experiments.application.services.experiment_service import ExperimentService
from modules.experiments.domain.entities.experiment_run import ExperimentRun


class GetExperimentRunsQuery:
    def __init__(self, service: ExperimentService | None = None):
        self.service = service or ExperimentService()

    def execute(self, experiment_id: str) -> list[ExperimentRun]:
        return self.service.get_runs(experiment_id)