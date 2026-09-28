from __future__ import annotations


class ExperimentError(Exception):
    """Base exception for all experiments-domain errors."""


class InvalidExperimentError(ExperimentError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class ExperimentNotFoundError(ExperimentError):
    pass


class ExperimentStateError(ExperimentError):
    """Operation not allowed in the experiment's current status."""