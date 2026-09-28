from __future__ import annotations

from sqlmodel import Field, SQLModel


class StrategyRow(SQLModel, table=True):
    __tablename__ = "strategies"
    id: str = Field(primary_key=True)
    name: str = Field(default="", index=True)
    description: str = ""
    version: int = 1
    config_json: str = "{}"
    is_archived: bool = False
    created_at: str = ""
    updated_at: str = ""


class StrategyVersionRow(SQLModel, table=True):
    """Immutable snapshot written each time a new version is saved."""
    __tablename__ = "strategy_versions"
    id: int | None = Field(default=None, primary_key=True)
    strategy_id: str = Field(index=True)
    version: int = 1
    name: str = ""
    description: str = ""
    config_json: str = "{}"
    created_at: str = ""