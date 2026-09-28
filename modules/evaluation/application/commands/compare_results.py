from __future__ import annotations

from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun


class CompareResultsCommand:
    """Rank an experiment's strategies by a metric (latest evaluation of each)."""

    def __init__(self, service: EvaluationService | None = None):
        self.service = service or EvaluationService()

    def execute(self, dataset_id: str, experiment_id: str, sort_by: str = "mrr") -> list[EvaluationRun]:
        return self.service.compare(dataset_id, experiment_id, sort_by)
