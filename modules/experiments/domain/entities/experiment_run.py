from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ExperimentRun:
    """One strategy (pinned version) executed within an experiment."""

    id: str = field(default_factory=_new_id)
    experiment_id: str = ""
    position: int = 0
    strategy_id: str = ""
    strategy_version: int = 1
    status: ExperimentStatus = ExperimentStatus.PENDING
    pipeline_run_id: str = ""   # RunRow id in the legacy pipeline tables (visible in Streamlit)
    result: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0

    def start(self) -> None:
        self.status = ExperimentStatus.RUNNING
        self.started_at = _utcnow()

    def complete(self, result: dict[str, Any], duration_seconds: float = 0.0) -> None:
        self.status = ExperimentStatus.COMPLETED
        self.result = result
        self.pipeline_run_id = str(result.get("pipeline_run_id", ""))
        self.duration_seconds = duration_seconds
        self.finished_at = _utcnow()

    def fail(self, error_message: str, duration_seconds: float = 0.0) -> None:
        self.status = ExperimentStatus.FAILED
        self.error_message = error_message
        self.duration_seconds = duration_seconds
        self.finished_at = _utcnow()

    def cancel(self) -> None:
        self.status = ExperimentStatus.CANCELLED
        self.finished_at = _utcnow()