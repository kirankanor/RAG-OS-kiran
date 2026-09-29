from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.artifacts.domain.value_objects.artifact_status import ArtifactStatus
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Artifact:
    """A generated file (report, code, package) derived from something else, e.g. a decision,
    strategy or project (`source_type` + `source_id`). Metadata only; bytes live in the blob store."""

    id: str = field(default_factory=_new_id)
    type: ArtifactType = ArtifactType.REPORT
    name: str = ""
    source_type: str = ""
    source_id: str = ""
    status: ArtifactStatus = ArtifactStatus.PENDING
    filename: str = ""
    storage_key: str = ""
    size_bytes: int = 0
    content_hash: str = ""
    note: str = ""
    error_message: str = ""
    created_at: str = field(default_factory=_utcnow)
    completed_at: str = ""

    def complete(self, storage_key: str, size_bytes: int, content_hash: str) -> None:
        self.status = ArtifactStatus.COMPLETED
        self.storage_key = storage_key
        self.size_bytes = size_bytes
        self.content_hash = content_hash
        self.completed_at = _utcnow()

    def fail(self, error_message: str) -> None:
        self.status = ArtifactStatus.FAILED
        self.error_message = error_message
        self.completed_at = _utcnow()
