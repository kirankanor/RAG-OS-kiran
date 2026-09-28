from __future__ import annotations

from enum import Enum


class ExperimentStatus(str, Enum):
    """Used for both an Experiment and each of its ExperimentRuns."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in (ExperimentStatus.COMPLETED, ExperimentStatus.FAILED, ExperimentStatus.CANCELLED)