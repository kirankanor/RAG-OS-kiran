from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Organization:
    """A group of users. Membership is stored on the user (User.organization_id),
    so a user belongs to at most one organization for now."""

    id: str = field(default_factory=_new_id)
    name: str = ""
    owner_id: str = ""
    created_at: str = field(default_factory=_utcnow)
