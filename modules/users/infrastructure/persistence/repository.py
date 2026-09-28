from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from modules.users.domain.entities.organization import Organization
from modules.users.domain.entities.user import User, UserRole
from modules.users.domain.exceptions import EmailAlreadyRegisteredError
from modules.users.domain.value_objects.user_id import UserId
from modules.users.infrastructure.persistence.models import OrganizationRow, UserRow
from shared.infrastructure.database.db_models import get_session


def _user_to_row(user: User) -> UserRow:
    return UserRow(id=str(user.id), email=user.email, password_hash=user.password_hash,
                   display_name=user.display_name, role=user.role.value,
                   organization_id=user.organization_id, is_active=user.is_active,
                   created_at=user.created_at)


def _row_to_user(row: UserRow) -> User:
    return User(id=UserId(row.id), email=row.email, password_hash=row.password_hash,
                display_name=row.display_name, role=UserRole(row.role),
                organization_id=row.organization_id, is_active=row.is_active,
                created_at=row.created_at)


def _row_to_org(row: OrganizationRow) -> Organization:
    return Organization(id=row.id, name=row.name, owner_id=row.owner_id, created_at=row.created_at)


class UserRepository:
    """SQLModel-backed persistence for users and organizations. Concrete class
    (no domain port): the users domain has no repositories/ folder in the plan."""

    def add_user(self, user: User) -> None:
        with get_session() as session:
            session.add(_user_to_row(user))
            try:
                session.commit()
            except IntegrityError as e:
                session.rollback()
                raise EmailAlreadyRegisteredError(f"Email already registered: {user.email}") from e

    def update_user(self, user: User) -> None:
        with get_session() as session:
            session.merge(_user_to_row(user))
            session.commit()

    def get_user(self, user_id: str) -> User | None:
        with get_session() as session:
            row = session.get(UserRow, user_id)
        return _row_to_user(row) if row else None

    def get_user_by_email(self, email: str) -> User | None:
        with get_session() as session:
            row = session.exec(select(UserRow).where(UserRow.email == email.strip().lower())).first()
        return _row_to_user(row) if row else None

    def add_organization(self, org: Organization) -> None:
        with get_session() as session:
            session.add(OrganizationRow(id=org.id, name=org.name, owner_id=org.owner_id,
                                        created_at=org.created_at))
            session.commit()

    def get_organization(self, org_id: str) -> Organization | None:
        with get_session() as session:
            row = session.get(OrganizationRow, org_id)
        return _row_to_org(row) if row else None
