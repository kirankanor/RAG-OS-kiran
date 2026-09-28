from __future__ import annotations

from sqlmodel import Field, SQLModel


class AnalysisRunRow(SQLModel, table=True):
    __tablename__ = "analysis_runs"
    id: str = Field(primary_key=True)
    name: str = ""
    sources_json: str = "[]"
    status: str = "pending"
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""


class CorpusProfileRow(SQLModel, table=True):
    __tablename__ = "corpus_profiles"
    id: str = Field(primary_key=True)
    analysis_run_id: str = Field(default="", index=True)
    profile_json: str = "{}"
    created_at: str = ""
