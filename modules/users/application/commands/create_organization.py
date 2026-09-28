from __future__ import annotations

from modules.users.application.services.user_service import UserService
from modules.users.domain.entities.organization import Organization


class CreateOrganizationCommand:
    """Create an organization owned by an existing user (who joins it)."""

    def __init__(self, service: UserService | None = None):
        self.service = service or UserService()

    def execute(self, name: str, owner_id: str) -> Organization:
        return self.service.create_organization(name, owner_id)
