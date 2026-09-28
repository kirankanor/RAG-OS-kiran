from __future__ import annotations

from sqlmodel import Field, SQLModel


class UserRow(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str = ""
    display_name: str = ""
    role: str = "member"
    organization_id: str = Field(default="", index=True)
    is_active: bool = True
    created_at: str = ""


class OrganizationRow(SQLModel, table=True):
    __tablename__ = "organizations"
    id: str = Field(primary_key=True)
    name: str = ""
    owner_id: str = Field(default="", index=True)
    created_at: str = ""
