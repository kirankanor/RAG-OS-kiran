from __future__ import annotations

from dataclasses import dataclass
from operator import ge, le
from typing import Any

METRICS: tuple[str, ...] = ("quality", "latency", "cost")
_COMPARE = {"<=": le, ">=": ge}


@dataclass(frozen=True)
class Constraint:
    """A hard requirement on a raw candidate value: quality (0..1), latency (seconds when
    every run was measured, otherwise relative units) or cost (relative units).
    Candidates that violate one are ranked below all that satisfy every constraint."""

    metric: str
    operator: str
    value: float

    def __post_init__(self) -> None:
        if self.metric not in METRICS:
            raise ValueError(f"Unknown constraint metric '{self.metric}'. Available: {list(METRICS)}")
        if self.operator not in _COMPARE:
            raise ValueError(f"Unknown constraint operator '{self.operator}'. Use '<=' or '>='.")

    def is_satisfied(self, actual: float) -> bool:
        return _COMPARE[self.operator](actual, self.value)

    def describe_violation(self, actual: float) -> str:
        return f"{self.metric} {actual:.3g} violates {self.metric} {self.operator} {self.value:g}"

    def to_dict(self) -> dict[str, Any]:
        return {"metric": self.metric, "operator": self.operator, "value": self.value}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Constraint:
        return cls(metric=d["metric"], operator=d["operator"], value=float(d["value"]))
