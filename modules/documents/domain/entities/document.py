from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.documents.domain.entities.document_version import DocumentVersion
from modules.documents.domain.events.document_events import (
    DocumentDeleted, DocumentEvent, DocumentUploaded, DocumentVersionCreated,
)
from modules.documents.domain.exceptions import DocumentStateError, InvalidDocumentError
from modules.documents.domain.value_objects.document_id import DocumentId
from modules.documents.domain.value_objects.document_status import DocumentStatus


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Document:
    """Aggregate root: a named file with an append-only list of versions. Metadata only;
    the bytes live in the blob store and parsing belongs to ingestion. State changes queue
    domain events in `pending_events` (never persisted); the service publishes them."""

    id: DocumentId = field(default_factory=DocumentId.new)
    name: str = ""
    filename: str = ""  # filename of the current version
    status: DocumentStatus = DocumentStatus.ACTIVE
    versions: list[DocumentVersion] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
    deleted_at: str = ""
    pending_events: list[DocumentEvent] = field(default_factory=list, repr=False, compare=False)

    @property
    def current_version(self) -> DocumentVersion | None:
        return self.versions[-1] if self.versions else None

    @property
    def is_deleted(self) -> bool:
        return self.status == DocumentStatus.DELETED

    def version(self, number: int) -> DocumentVersion | None:
        return next((v for v in self.versions if v.number == number), None)

    def add_version(self, version: DocumentVersion) -> None:
        if self.is_deleted:
            raise DocumentStateError("Cannot add a version to a deleted document.")
        expected = len(self.versions) + 1
        if version.number != expected:
            raise InvalidDocumentError(f"Expected version {expected}, got {version.number}.")
        self.versions.append(version)
        self.filename = version.filename
        self.updated_at = _utcnow()
        event = DocumentUploaded if expected == 1 else DocumentVersionCreated
        self.pending_events.append(event(document_id=str(self.id), version=expected,
                                         content_hash=version.content_hash.value))

    def delete(self) -> bool:
        """Soft delete. Returns False (and does nothing) if already deleted."""
        if self.is_deleted:
            return False
        self.status = DocumentStatus.DELETED
        self.deleted_at = self.updated_at = _utcnow()
        self.pending_events.append(DocumentDeleted(document_id=str(self.id)))
        return True

    def pull_events(self) -> list[DocumentEvent]:
        events, self.pending_events = self.pending_events, []
        return events
