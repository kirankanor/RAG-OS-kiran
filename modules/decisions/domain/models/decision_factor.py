from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any

FACTOR_QUALITY = "quality"
FACTOR_LATENCY = "latency"
FACTOR_COST = "cost"
FACTOR_CORPUS_FIT = "corpus_fit"
FACTORS: tuple[str, ...] = (FACTOR_QUALITY, FACTOR_LATENCY, FACTOR_COST, FACTOR_CORPUS_FIT)


@dataclass(frozen=True)
class DecisionFactor:
    """One scored dimension of a candidate. `value` is the raw number (seconds, cost
    units, metric value); `score` is normalized to 0..1 with higher always better."""

    name: str
    value: float = 0.0
    score: float = 0.0
    weight: float = 0.0
    unit: str = ""
    note: str = ""

    @property
    def weighted_score(self) -> float:
        return self.weight * self.score

    @property
    def display(self) -> str:
        sep = " " if len(self.unit) > 1 else ""
        return f"{self.value:.3g}{sep}{self.unit}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DecisionFactor:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})
