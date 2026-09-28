from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class DocumentEvent:
    document_id: str
    occurred_at: str = field(default_factory=_utcnow)


@dataclass(frozen=True)
class DocumentUploaded(DocumentEvent):
    version: int = 1
    content_hash: str = ""


@dataclass(frozen=True)
class DocumentVersionCreated(DocumentEvent):
    version: int = 2
    content_hash: str = ""


@dataclass(frozen=True)
class DocumentDeleted(DocumentEvent):
    pass
