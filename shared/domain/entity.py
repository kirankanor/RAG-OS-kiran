from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Entity:
    """Marker base for entities with identity + lifecycle timestamps. Existing entities
    (Strategy, Document, Project, ...) already carry their own id/created_at/updated_at by
    convention; this base is available for new ones that want it without duplicating the
    boilerplate, not a required parent class."""

    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def touch(self) -> None:
        self.updated_at = _utcnow()
