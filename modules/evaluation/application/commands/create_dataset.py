from __future__ import annotations

from modules.evaluation.application.services.evaluation_service import EvaluationService
from modules.evaluation.domain.entities.evaluation_dataset import EvaluationDataset, EvaluationQuery


class CreateDatasetCommand:
    def __init__(self, service: EvaluationService | None = None):
        self.service = service or EvaluationService()

    def execute(self, name: str, queries: list[EvaluationQuery | dict],
                description: str = "") -> EvaluationDataset:
        return self.service.create_dataset(name, queries, description)
