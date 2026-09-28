from __future__ import annotations


class ProjectError(Exception):
    """Base exception for all projects-domain errors."""


class InvalidProjectError(ProjectError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class ProjectNotFoundError(ProjectError):
    pass


class ProjectStateError(ProjectError):
    """Operation not allowed in the project's current status (archived or deleted)."""
