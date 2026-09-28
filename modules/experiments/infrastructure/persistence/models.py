from __future__ import annotations

from sqlmodel import Field, SQLModel


class ExperimentRow(SQLModel, table=True):
    __tablename__ = "experiments"
    id: str = Field(primary_key=True)
    name: str = Field(default="", index=True)
    description: str = ""
    config_json: str = "{}"
    strategies_json: str = "[]"
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""


class ExperimentRunRow(SQLModel, table=True):
    __tablename__ = "experiment_runs"
    id: str = Field(primary_key=True)
    experiment_id: str = Field(index=True)
    position: int = 0
    strategy_id: str = ""
    strategy_version: int = 1
    status: str = "pending"
    pipeline_run_id: str = ""
    result_json: str = "{}"
    error_message: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0