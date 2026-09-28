from __future__ import annotations

from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun


class GetEvaluationQuery:
    def __init__(self, service: EvaluationService | None = None):
        self.service = service or EvaluationService()

    def execute(self, evaluation_run_id: str) -> EvaluationRun:
        return self.service.get_run(evaluation_run_id)

    def for_experiment(self, experiment_id: str, dataset_id: str = "") -> list[EvaluationRun]:
        return self.service.list_runs(dataset_id=dataset_id, experiment_id=experiment_id)
