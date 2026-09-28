from __future__ import annotations

from sqlmodel import Field, SQLModel


class DocumentRecordRow(SQLModel, table=True):
    """Named *_records because the legacy pipeline already owns the 'documents' table (DocumentRow)."""
    __tablename__ = "document_records"
    id: str = Field(primary_key=True)
    name: str = Field(default="", index=True)
    filename: str = ""
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    deleted_at: str = ""


class DocumentVersionRow(SQLModel, table=True):
    """Immutable: one row per version, never updated."""
    __tablename__ = "document_versions"
    id: int | None = Field(default=None, primary_key=True)
    document_id: str = Field(index=True)
    number: int = 1
    content_hash: str = Field(default="", index=True)
    size_bytes: int = 0
    filename: str = ""
    storage_key: str = ""
    note: str = ""
    created_at: str = ""
