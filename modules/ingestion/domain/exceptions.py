from __future__ import annotations


class IngestionError(Exception):
    """Base exception for all ingestion-domain errors."""


class UnsupportedFileTypeError(IngestionError):
    """Raised when no parser is configured/available for a file's extension."""


class ValidationFailedError(IngestionError):
    """Raised when a Validator rejects a target and the pipeline can't proceed."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class NormalizationError(IngestionError):
    """Raised when a Normalizer fails to process a CanonicalDocument."""


class DocumentStorageError(IngestionError):
    """Raised when a DocumentStorage implementation fails to save/load a document."""


class DocumentNotFoundError(DocumentStorageError):
    """Raised when DocumentStorage.load() is called with an unknown document_id."""


class IngestionJobFailedError(IngestionError):
    """Raised when an IngestionJob's pipeline stage hits an unrecoverable error."""

    def __init__(self, message: str, job_id: str = "", stage: str = ""):
        super().__init__(message)
        self.job_id = job_id
        self.stage = stage