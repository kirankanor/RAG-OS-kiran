from __future__ import annotations

from modules.artifacts.application.services.report_service import ReportService
from modules.artifacts.domain.entities.artifact import Artifact


class GenerateReportCommand:
    """Markdown report for a saved decision. summarize_with: optional generator name for an LLM summary."""

    def __init__(self, service: ReportService | None = None):
        self.service = service or ReportService()

    def execute(self, decision_id: str, summarize_with: str = "") -> Artifact:
        return self.service.generate_decision_report(decision_id, summarize_with)
