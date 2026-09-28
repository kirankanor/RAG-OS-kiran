from __future__ import annotations


class DecisionError(Exception):
    """Base exception for all decisions-domain errors."""


class InvalidDecisionError(DecisionError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class DecisionNotFoundError(DecisionError):
    pass
