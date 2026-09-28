from __future__ import annotations

from sqlmodel import Field, SQLModel


class DecisionRow(SQLModel, table=True):
    __tablename__ = "decisions"
    id: str = Field(primary_key=True)
    experiment_id: str = Field(default="", index=True)
    dataset_id: str = Field(default="", index=True)
    corpus_profile_id: str = ""
    decision_json: str = "{}"
    created_at: str = ""
