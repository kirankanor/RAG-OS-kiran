from __future__ import annotations

from sqlmodel import Field, SQLModel


class EvaluationDatasetRow(SQLModel, table=True):
    __tablename__ = "evaluation_datasets"
    id: str = Field(primary_key=True)
    name: str = Field(default="", index=True)
    description: str = ""
    queries_json: str = "[]"
    created_at: str = ""


class EvaluationRunRow(SQLModel, table=True):
    __tablename__ = "evaluation_runs"
    id: str = Field(primary_key=True)
    dataset_id: str = Field(default="", index=True)
    experiment_id: str = Field(default="", index=True)
    experiment_run_id: str = ""
    strategy_id: str = ""
    strategy_version: int = 1
    pipeline_run_id: str = ""
    status: str = "completed"
    result_json: str = "{}"
    error_message: str = ""
    created_at: str = ""
