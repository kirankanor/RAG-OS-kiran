from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from modules.decisions.application.services.recommendation_service import RecommendationService
from modules.decisions.domain.entities.decision import Decision
from modules.decisions.domain.models.constraint import Constraint


class MakeDecisionCommand:
    """Recommend a strategy from a finished experiment that has been evaluated against a
    dataset. Runs synchronously. Optional: a corpus profile id (adds corpus fit), weights
    (factors: quality, latency, cost, corpus_fit), hard constraints, and a generator name
    for an LLM-written explanation."""

    def __init__(self, service: RecommendationService | None = None):
        self.service = service or RecommendationService()

    def execute(self, experiment_id: str, dataset_id: str, corpus_profile_id: str = "",
                weights: Mapping[str, float] | None = None,
                constraints: Sequence[Constraint | dict[str, Any]] | None = None,
                explain_with: str = "") -> Decision:
        return self.service.make_decision(experiment_id, dataset_id, corpus_profile_id, weights,
                                          constraints, explain_with)
