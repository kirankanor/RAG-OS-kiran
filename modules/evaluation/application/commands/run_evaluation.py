from __future__ import annotations

from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun


class RunEvaluationCommand:
    """Score a finished experiment against a dataset. Runs synchronously."""

    def __init__(self, service: EvaluationService | None = None):
        self.service = service or EvaluationService()

    def execute(self, dataset_id: str, experiment_id: str, k: int | None = None) -> list[EvaluationRun]:
        return self.service.evaluate(dataset_id, experiment_id, k)
