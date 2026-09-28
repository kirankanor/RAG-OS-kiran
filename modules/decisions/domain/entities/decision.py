from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from modules.decisions.domain.entities.recommendation import Recommendation
from modules.decisions.domain.models.constraint import Constraint
from modules.decisions.domain.models.tradeoff import Tradeoff


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Decision:
    """Aggregate: which strategy of an experiment to pick, and why. Recommendations are
    ranked (eligible ones first). `weights` are the normalized weights actually used."""

    id: str = field(default_factory=_new_id)
    experiment_id: str = ""
    dataset_id: str = ""
    corpus_profile_id: str = ""
    weights: dict[str, float] = field(default_factory=dict)
    constraints: list[Constraint] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    tradeoffs: list[Tradeoff] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    explanation: str = ""
    created_at: str = field(default_factory=_utcnow)

    @property
    def winner(self) -> Recommendation | None:
        return next((r for r in self.recommendations if r.eligible), None)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "experiment_id": self.experiment_id, "dataset_id": self.dataset_id,
                "corpus_profile_id": self.corpus_profile_id, "weights": dict(self.weights),
                "constraints": [c.to_dict() for c in self.constraints],
                "recommendations": [r.to_dict() for r in self.recommendations],
                "tradeoffs": [t.to_dict() for t in self.tradeoffs], "warnings": list(self.warnings),
                "explanation": self.explanation, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Decision:
        return cls(id=d.get("id", _new_id()), experiment_id=d.get("experiment_id", ""),
                   dataset_id=d.get("dataset_id", ""), corpus_profile_id=d.get("corpus_profile_id", ""),
                   weights=dict(d.get("weights", {})),
                   constraints=[Constraint.from_dict(c) for c in d.get("constraints", [])],
                   recommendations=[Recommendation.from_dict(r) for r in d.get("recommendations", [])],
                   tradeoffs=[Tradeoff.from_dict(t) for t in d.get("tradeoffs", [])],
                   warnings=list(d.get("warnings", [])), explanation=d.get("explanation", ""),
                   created_at=d.get("created_at", _utcnow()))
