from __future__ import annotations

from sqlmodel import select

from modules.decisions.domain.entities.decision import Decision
from modules.decisions.infrastructure.persistence.models import DecisionRow
from shared.infrastructure.database.db_models import dumps, get_session, loads


def _to_row(d: Decision) -> DecisionRow:
    return DecisionRow(id=d.id, experiment_id=d.experiment_id, dataset_id=d.dataset_id,
                       corpus_profile_id=d.corpus_profile_id, decision_json=dumps(d.to_dict()),
                       created_at=d.created_at)


def _from_row(row: DecisionRow) -> Decision:
    return Decision.from_dict(loads(row.decision_json))


class DecisionRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like the other modules."""

    def save(self, decision: Decision) -> None:
        with get_session() as session:
            session.merge(_to_row(decision))
            session.commit()

    def get(self, decision_id: str) -> Decision | None:
        with get_session() as session:
            row = session.get(DecisionRow, decision_id)
        return _from_row(row) if row else None

    def list(self, experiment_id: str = "") -> list[Decision]:
        """Newest first."""
        stmt = select(DecisionRow).order_by(DecisionRow.created_at.desc())
        if experiment_id:
            stmt = stmt.where(DecisionRow.experiment_id == experiment_id)
        with get_session() as session:
            return [_from_row(r) for r in session.exec(stmt)]
