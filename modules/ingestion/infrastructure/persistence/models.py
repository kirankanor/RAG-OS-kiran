from __future__ import annotations

from sqlmodel import Field, SQLModel


class IngestionRunRow(SQLModel, table=True):
    __tablename__ = "ingestion_runs"
    id: str = Field(primary_key=True)
    name: str = ""
    created_at: str = ""
    completed_at: str = ""


class IngestionJobRow(SQLModel, table=True):
    __tablename__ = "ingestion_jobs"
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    source_filename: str = ""
    status: str = "pending"
    stage: str = "uploaded"
    error_message: str = ""
    retry_count: int = 0
    created_at: str = ""
    updated_at: str = ""


class CanonicalDocumentRow(SQLModel, table=True):
    __tablename__ = "canonical_documents"
    id: str = Field(primary_key=True)
    source_document_id: str = Field(index=True, default="")
    source_filename: str = ""
    pages_json: str = "[]"
    stage: str = "uploaded"
    version_json: str = "{}"
    created_at: str = ""
