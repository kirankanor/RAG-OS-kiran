from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class DomainEvent:
    """Base for every module's *Event dataclasses (ProjectCreated, DocumentDeleted, ...).
    Existing event classes already follow this shape by convention; this formalizes it as
    a real base so cross-cutting code (an event bus, logging) can type against it."""

    occurred_at: str = field(default_factory=_utcnow)
