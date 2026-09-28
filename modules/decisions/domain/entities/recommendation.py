from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from modules.decisions.domain.models.decision_factor import DecisionFactor


@dataclass
class Recommendation:
    """One candidate strategy (pinned version) with its ranking and score breakdown."""

    strategy_id: str
    strategy_version: int = 1
    strategy_name: str = ""
    rank: int = 0
    total_score: float = 0.0
    eligible: bool = True   # False if it violates a hard constraint
    factors: list[DecisionFactor] = field(default_factory=list)
    violated_constraints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def factor(self, name: str) -> DecisionFactor | None:
        return next((f for f in self.factors if f.name == name), None)

    def to_dict(self) -> dict[str, Any]:
        return {"strategy_id": self.strategy_id, "strategy_version": self.strategy_version,
                "strategy_name": self.strategy_name, "rank": self.rank, "total_score": self.total_score,
                "eligible": self.eligible, "factors": [f.to_dict() for f in self.factors],
                "violated_constraints": list(self.violated_constraints), "warnings": list(self.warnings)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Recommendation:
        return cls(strategy_id=d["strategy_id"], strategy_version=d.get("strategy_version", 1),
                   strategy_name=d.get("strategy_name", ""), rank=d.get("rank", 0),
                   total_score=d.get("total_score", 0.0), eligible=d.get("eligible", True),
                   factors=[DecisionFactor.from_dict(f) for f in d.get("factors", [])],
                   violated_constraints=list(d.get("violated_constraints", [])),
                   warnings=list(d.get("warnings", [])))
