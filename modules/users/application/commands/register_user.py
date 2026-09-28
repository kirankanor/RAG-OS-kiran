from __future__ import annotations

from modules.users.application.services.user_service import UserService
from modules.users.domain.entities.user import User


class RegisterUserCommand:
    """Register a new user. Returns the User entity (contains password_hash --
    map to a response schema before exposing over an API)."""

    def __init__(self, service: UserService | None = None):
        self.service = service or UserService()

    def execute(self, email: str, password: str, display_name: str = "",
                organization_id: str = "") -> User:
        return self.service.register(email, password, display_name, organization_id)
