from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from modules.evaluation.domain.models.evaluation_result import EvaluationResult


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


class EvaluationStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EvaluationRun:
    """One dataset scored against one ExperimentRun (one strategy)."""

    id: str = field(default_factory=_new_id)
    dataset_id: str = ""
    experiment_id: str = ""
    experiment_run_id: str = ""
    strategy_id: str = ""
    strategy_version: int = 1
    pipeline_run_id: str = ""
    status: EvaluationStatus = EvaluationStatus.COMPLETED
    result: EvaluationResult = field(default_factory=EvaluationResult)
    error_message: str = ""
    created_at: str = field(default_factory=_utcnow)

    def complete(self, result: EvaluationResult) -> None:
        self.status = EvaluationStatus.COMPLETED
        self.result = result

    def fail(self, error_message: str) -> None:
        self.status = EvaluationStatus.FAILED
        self.error_message = error_message
