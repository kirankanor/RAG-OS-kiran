from __future__ import annotations


class DocumentError(Exception):
    """Base exception for all documents-domain errors."""


class InvalidDocumentError(DocumentError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class UnsupportedDocumentTypeError(InvalidDocumentError):
    pass


class DocumentNotFoundError(DocumentError):
    pass


class DocumentVersionNotFoundError(DocumentError):
    pass


class DocumentStateError(DocumentError):
    """Operation not allowed in the document's current status (e.g. versioning a deleted document)."""


class DuplicateDocumentError(DocumentError):
    """The same content is already the current version of an active document."""

    def __init__(self, message: str, existing_document_id: str = ""):
        super().__init__(message)
        self.existing_document_id = existing_document_id


class UnchangedContentError(DocumentError):
    """A new version was requested with content identical to the current version."""


class DocumentStorageError(DocumentError):
    """The stored file is missing or a storage key is unsafe."""
