from __future__ import annotations

import re

from sqlmodel import SQLModel

from modules.users.domain.entities.organization import Organization
from modules.users.domain.entities.user import User
from modules.users.domain.exceptions import (
    AlreadyInOrganizationError, InvalidCredentialsError, InvalidEmailError, InvalidTokenError,
    OrganizationNotFoundError, UserError, UserNotFoundError, WeakPasswordError,
)
# Importing models registers the users/organizations tables on SQLModel.metadata.
from modules.users.infrastructure.persistence import models as _models  # noqa: F401
from modules.users.infrastructure.auth.jwt import create_access_token, decode_access_token
from modules.users.infrastructure.auth.password import hash_password, verify_password
from modules.users.infrastructure.persistence.repository import UserRepository
from shared.infrastructure.database.db_models import get_engine

MIN_PASSWORD_LENGTH = 8
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class UserService:
    def __init__(self, repository: UserRepository | None = None):
        _ensure_tables()
        self.repository = repository or UserRepository()
        self._dummy_hash: str | None = None

    def register(self, email: str, password: str, display_name: str = "",
                 organization_id: str = "") -> User:
        email = email.strip().lower()
        if not _EMAIL_RE.match(email):
            raise InvalidEmailError(f"Invalid email address: '{email}'")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if organization_id and self.repository.get_organization(organization_id) is None:
            raise OrganizationNotFoundError(f"No organization with id '{organization_id}'")
        user = User(email=email, password_hash=hash_password(password),
                    display_name=display_name or email.split("@")[0],
                    organization_id=organization_id)
        self.repository.add_user(user)  # raises EmailAlreadyRegisteredError on duplicate
        return user

    def authenticate(self, email: str, password: str) -> str:
        """Returns a JWT access token, or raises InvalidCredentialsError."""
        user = self.repository.get_user_by_email(email)
        if user is None:
            # Burn comparable time so response timing doesn't reveal which emails exist.
            if self._dummy_hash is None:
                self._dummy_hash = hash_password("dummy-password")
            verify_password(password, self._dummy_hash)
            raise InvalidCredentialsError("Invalid email or password.")
        if not verify_password(password, user.password_hash) or not user.is_active:
            raise InvalidCredentialsError("Invalid email or password.")
        return create_access_token(str(user.id), user.role.value)

    def verify_token(self, token: str) -> User:
        payload = decode_access_token(token)
        user = self.repository.get_user(payload.get("sub", ""))
        if user is None or not user.is_active:
            raise InvalidTokenError("Token refers to an unknown or inactive user.")
        return user

    def get_user(self, user_id: str) -> User:
        user = self.repository.get_user(user_id)
        if user is None:
            raise UserNotFoundError(f"No user with id '{user_id}'")
        return user

    def create_organization(self, name: str, owner_id: str) -> Organization:
        name = name.strip()
        if not name:
            raise UserError("Organization name is required.")
        owner = self.get_user(owner_id)
        if owner.organization_id:
            raise AlreadyInOrganizationError("User already belongs to an organization.")
        org = Organization(name=name, owner_id=str(owner.id))
        self.repository.add_organization(org)
        owner.join_organization(org.id)
        self.repository.update_user(owner)
        return org
