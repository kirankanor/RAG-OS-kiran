from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.ingestion.domain.value_objects.ingestion_status import IngestionStatus
from modules.ingestion.domain.value_objects.processing_stage import ProcessingStage


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class IngestionJob:
    """Tracks a single source file's progress through the ingestion pipeline."""

    id: str = field(default_factory=_new_id)
    run_id: str = ""
    source_filename: str = ""
    status: IngestionStatus = IngestionStatus.PENDING
    stage: ProcessingStage = ProcessingStage.UPLOADED
    error_message: str = ""
    retry_count: int = 0
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def start(self) -> None:
        self.status = IngestionStatus.RUNNING
        self.updated_at = _utcnow()

    def advance(self, stage: ProcessingStage) -> None:
        self.stage = stage
        self.updated_at = _utcnow()

    def fail(self, error_message: str) -> None:
        self.status = IngestionStatus.FAILED
        self.error_message = error_message
        self.updated_at = _utcnow()

    def retry(self) -> None:
        self.status = IngestionStatus.RETRYING
        self.retry_count += 1
        self.error_message = ""
        self.updated_at = _utcnow()

    def complete(self) -> None:
        self.status = IngestionStatus.COMPLETED
        self.stage = ProcessingStage.COMPLETED
        self.updated_at = _utcnow()
