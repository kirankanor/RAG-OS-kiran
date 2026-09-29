from __future__ import annotations


class ArtifactError(Exception):
    """Base exception for all artifacts-domain errors."""


class InvalidArtifactError(ArtifactError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class ArtifactNotFoundError(ArtifactError):
    pass


class ArtifactStorageError(ArtifactError):
    """The stored file is missing or a storage key is unsafe."""


class ArtifactGenerationError(ArtifactError):
    """Generating or storing the artifact's content failed."""
