from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricResult:
    """One metric: its mean over evaluated queries plus the per-query values."""

    name: str = ""
    value: float = 0.0
    per_query: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "per_query": dict(self.per_query)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> MetricResult:
        return cls(name=d.get("name", ""), value=float(d.get("value", 0.0)),
                   per_query={k: float(v) for k, v in d.get("per_query", {}).items()})
