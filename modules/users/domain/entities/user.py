from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from modules.users.domain.value_objects.user_id import UserId


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


@dataclass
class User:
    id: UserId = field(default_factory=UserId.new)
    email: str = ""
    password_hash: str = field(default="", repr=False)
    display_name: str = ""
    role: UserRole = UserRole.MEMBER
    organization_id: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow)

    def join_organization(self, organization_id: str) -> None:
        self.organization_id = organization_id

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
