from __future__ import annotations

from modules.decisions.application.services.recommendation_service import RecommendationService
from modules.decisions.domain.entities.decision import Decision


class GetDecisionQuery:
    def __init__(self, service: RecommendationService | None = None):
        self.service = service or RecommendationService()

    def execute(self, decision_id: str) -> Decision:
        return self.service.get(decision_id)

    def for_experiment(self, experiment_id: str) -> list[Decision]:
        return self.service.list(experiment_id)

    def list(self) -> list[Decision]:
        return self.service.list()
