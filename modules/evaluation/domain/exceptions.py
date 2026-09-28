from __future__ import annotations


class EvaluationError(Exception):
    """Base exception for all evaluation-domain errors."""


class InvalidDatasetError(EvaluationError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class DatasetNotFoundError(EvaluationError):
    pass


class EvaluationRunNotFoundError(EvaluationError):
    pass


class EvaluationStateError(EvaluationError):
    """Operation not allowed in the source experiment's current status."""
