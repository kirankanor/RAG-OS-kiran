from __future__ import annotations


class CorpusAnalysisError(Exception):
    """Base exception for all corpus_analysis-domain errors."""


class InvalidCorpusError(CorpusAnalysisError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class ProfileNotFoundError(CorpusAnalysisError):
    pass


class AnalysisRunNotFoundError(CorpusAnalysisError):
    pass
