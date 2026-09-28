from __future__ import annotations

from collections.abc import Sequence

from modules.corpus_analysis.application.services.corpus_analysis_service import CorpusAnalysisService
from modules.corpus_analysis.domain.entities.corpus_profile import CorpusProfile


class AnalyzeCorpusCommand:
    """Analyze a set of files and persist the resulting CorpusProfile. Runs synchronously.
    analyzers=None runs all of them (size, structure, language, duplicates, tables, ocr)."""

    def __init__(self, service: CorpusAnalysisService | None = None):
        self.service = service or CorpusAnalysisService()

    def execute(self, file_paths: Sequence[str], name: str = "",
                analyzers: Sequence[str] | None = None) -> CorpusProfile:
        return self.service.analyze_files(file_paths, name, analyzers)
