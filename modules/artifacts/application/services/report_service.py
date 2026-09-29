from __future__ import annotations

from modules.artifacts.application.services.artifact_service import ArtifactService
from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.exceptions import InvalidArtifactError
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
from modules.artifacts.infrastructure.generators.markdown_generator import render_decision_report
from modules.artifacts.infrastructure.llm.artifact_llm_generator import ArtifactLlmGenerator
from modules.decisions.application.services.recommendation_service import RecommendationService
from shared.ai.llm import generator_registry


class ReportService:
    def __init__(self, artifacts: ArtifactService | None = None,
                 decisions: RecommendationService | None = None):
        self.artifacts = artifacts or ArtifactService()
        self.decisions = decisions or RecommendationService()

    def generate_decision_report(self, decision_id: str, summarize_with: str = "") -> Artifact:
        """Markdown report of a saved Decision. `summarize_with` is a generator name (e.g.
        'groq_chat') for an LLM summary on top; empty = no summary."""
        summarizer = self._summarizer(summarize_with)
        decision = self.decisions.get(decision_id)  # raises DecisionNotFoundError
        summary = summarizer.summarize(render_decision_report(decision)) if summarizer else ""
        md = render_decision_report(decision, summary)
        return self.artifacts.record(
            ArtifactType.REPORT, f"Decision report {decision.id}", f"decision-{decision.id}-report.md",
            md.encode("utf-8"), source_type="decision", source_id=decision.id)

    @staticmethod
    def _summarizer(name: str) -> ArtifactLlmGenerator | None:
        if not name:
            return None
        if name not in generator_registry.names():
            raise InvalidArtifactError(f"Unknown generator '{name}'. Available: {generator_registry.names()}")
        return ArtifactLlmGenerator(generator_registry.create(name))
