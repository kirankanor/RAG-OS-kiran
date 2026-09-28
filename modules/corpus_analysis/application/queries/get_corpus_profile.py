from __future__ import annotations

from modules.corpus_analysis.application.services.corpus_analysis_service import CorpusAnalysisService
from modules.corpus_analysis.domain.entities.corpus_profile import CorpusProfile


class GetCorpusProfileQuery:
    def __init__(self, service: CorpusAnalysisService | None = None):
        self.service = service or CorpusAnalysisService()

    def execute(self, profile_id: str) -> CorpusProfile:
        return self.service.get_profile(profile_id)

    def for_run(self, run_id: str) -> CorpusProfile:
        return self.service.get_profile_for_run(run_id)

    def list(self) -> list[CorpusProfile]:
        return self.service.list_profiles()
