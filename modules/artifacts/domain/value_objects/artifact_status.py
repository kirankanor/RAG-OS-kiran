from __future__ import annotations

from enum import Enum


class ArtifactStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in (ArtifactStatus.COMPLETED, ArtifactStatus.FAILED)
