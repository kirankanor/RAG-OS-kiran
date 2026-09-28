from __future__ import annotations

from sqlmodel import Field, SQLModel


class ProjectRow(SQLModel, table=True):
    __tablename__ = "projects"
    id: str = Field(primary_key=True)
    name: str = Field(default="", index=True)
    description: str = ""
    owner_id: str = Field(default="", index=True)
    status: str = Field(default="active", index=True)
    document_ids_json: str = "[]"
    experiment_ids_json: str = "[]"
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""
