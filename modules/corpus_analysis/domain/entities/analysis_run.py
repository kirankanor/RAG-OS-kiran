from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED)


@dataclass
class AnalysisRun:
    """One analysis invocation over a set of source files. Produces one CorpusProfile."""

    id: str = field(default_factory=_new_id)
    name: str = ""
    source_filenames: list[str] = field(default_factory=list)
    status: AnalysisStatus = AnalysisStatus.PENDING
    error_message: str = ""
    created_at: str = field(default_factory=_utcnow)
    completed_at: str = ""

    def start(self) -> None:
        self.status = AnalysisStatus.RUNNING

    def complete(self) -> None:
        self.status = AnalysisStatus.COMPLETED
        self.completed_at = _utcnow()

    def fail(self, error_message: str) -> None:
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = _utcnow()
