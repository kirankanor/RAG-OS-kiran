from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class EvaluationQuery:
    """A query plus the text snippets that a good retrieval must surface.
    Ground truth is text-based because chunk ids are random per pipeline run:
    a retrieved chunk matches snippet i if it contains it (case/whitespace-insensitive)."""

    query: str = ""
    relevant_texts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "relevant_texts": list(self.relevant_texts)}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> EvaluationQuery:
        return cls(query=d.get("query", ""), relevant_texts=list(d.get("relevant_texts", [])))


@dataclass
class EvaluationDataset:
    id: str = field(default_factory=_new_id)
    name: str = ""
    description: str = ""
    queries: list[EvaluationQuery] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("Dataset name is required.")
        if not self.queries:
            errors.append("At least one query is required.")
        seen: set[str] = set()
        for i, q in enumerate(self.queries):
            if not q.query.strip():
                errors.append(f"Query #{i + 1} is empty.")
            elif q.query in seen:
                errors.append(f"Duplicate query: '{q.query}'.")
            seen.add(q.query)
            if not any(t.strip() for t in q.relevant_texts):
                errors.append(f"Query #{i + 1} needs at least one non-empty relevant text.")
        return errors
