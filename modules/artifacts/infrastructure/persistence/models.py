from __future__ import annotations

from sqlmodel import Field, SQLModel


class ArtifactRow(SQLModel, table=True):
    __tablename__ = "artifacts"
    id: str = Field(primary_key=True)
    type: str = Field(default="report", index=True)
    name: str = ""
    source_type: str = Field(default="", index=True)
    source_id: str = Field(default="", index=True)
    status: str = "pending"
    filename: str = ""
    storage_key: str = ""
    size_bytes: int = 0
    content_hash: str = ""
    note: str = ""
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""
