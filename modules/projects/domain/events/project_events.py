from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ProjectEvent:
    project_id: str
    occurred_at: str = field(default_factory=_utcnow)


@dataclass(frozen=True)
class ProjectCreated(ProjectEvent):
    owner_id: str = ""


@dataclass(frozen=True)
class ProjectUpdated(ProjectEvent):
    changes: tuple[str, ...] = ()  # any of: name, description, documents, experiments, status


@dataclass(frozen=True)
class ProjectDeleted(ProjectEvent):
    pass
