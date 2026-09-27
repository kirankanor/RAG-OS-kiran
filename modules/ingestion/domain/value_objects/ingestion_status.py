from __future__ import annotations

from enum import Enum


class IngestionStatus(str, Enum):
    """Overall lifecycle status of an ingestion job/run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (IngestionStatus.COMPLETED, IngestionStatus.FAILED, IngestionStatus.CANCELLED)
