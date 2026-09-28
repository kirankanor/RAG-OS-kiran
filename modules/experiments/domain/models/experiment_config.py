from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StrategyRef:
    """Points at a saved Strategy. version=None means 'current' and is pinned at creation."""

    strategy_id: str
    version: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"strategy_id": self.strategy_id, "version": self.version}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StrategyRef:
        return cls(d["strategy_id"], d.get("version"))


@dataclass(frozen=True)
class ExperimentConfig:
    """What every strategy in the experiment is run against."""

    runner: str = "retrieval"          # "ingestion" | "retrieval" | "rag"
    file_paths: list[str] = field(default_factory=list)
    queries: list[str] = field(default_factory=list)
    top_k: int | None = None           # None = use each strategy's own retrieval.top_k
    generator_name: str = ""           # rag runner only
    generator_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"runner": self.runner, "file_paths": list(self.file_paths),
                "queries": list(self.queries), "top_k": self.top_k,
                "generator_name": self.generator_name,
                "generator_params": dict(self.generator_params)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ExperimentConfig:
        return cls(runner=d.get("runner", "retrieval"), file_paths=list(d.get("file_paths", [])),
                   queries=list(d.get("queries", [])), top_k=d.get("top_k"),
                   generator_name=d.get("generator_name", ""),
                   generator_params=dict(d.get("generator_params", {})))