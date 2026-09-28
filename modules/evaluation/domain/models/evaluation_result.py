from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from modules.evaluation.domain.models.metric_result import MetricResult


@dataclass
class EvaluationResult:
    k: int = 0
    num_queries: int = 0  # dataset queries actually found in the run's results
    metrics: list[MetricResult] = field(default_factory=list)

    def summary(self) -> dict[str, float]:
        return {m.name: m.value for m in self.metrics}

    def get(self, name: str) -> float | None:
        return self.summary().get(name)

    def to_dict(self) -> dict[str, Any]:
        return {"k": self.k, "num_queries": self.num_queries,
                "metrics": [m.to_dict() for m in self.metrics]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EvaluationResult:
        return cls(k=d.get("k", 0), num_queries=d.get("num_queries", 0),
                   metrics=[MetricResult.from_dict(m) for m in d.get("metrics", [])])
