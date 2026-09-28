from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.documents.domain.value_objects.document_hash import DocumentHash


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class DocumentVersion:
    """One immutable snapshot of a document's file. `storage_key` locates the bytes in the blob store."""

    number: int
    content_hash: DocumentHash
    size_bytes: int
    filename: str
    storage_key: str
    note: str = ""
    created_at: str = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Version number must be >= 1.")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be >= 0.")
