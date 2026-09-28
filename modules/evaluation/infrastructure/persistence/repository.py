from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import col, select

from modules.evaluation.domain.entities.evaluation_dataset import EvaluationDataset, EvaluationQuery
from modules.evaluation.domain.entities.evaluation_run import EvaluationRun, EvaluationStatus
from modules.evaluation.domain.models.evaluation_result import EvaluationResult
from modules.evaluation.infrastructure.persistence.models import EvaluationDatasetRow, EvaluationRunRow
from shared.infrastructure.database.db_models import ChunkRow, dumps, get_session, loads


def _dataset_to_row(d: EvaluationDataset) -> EvaluationDatasetRow:
    return EvaluationDatasetRow(id=d.id, name=d.name, description=d.description,
                                queries_json=dumps([q.to_dict() for q in d.queries]),
                                created_at=d.created_at)


def _row_to_dataset(r: EvaluationDatasetRow) -> EvaluationDataset:
    raw = loads(r.queries_json) or []
    return EvaluationDataset(id=r.id, name=r.name, description=r.description,
                             queries=[EvaluationQuery.from_dict(q) for q in raw],
                             created_at=r.created_at)


def _run_to_row(r: EvaluationRun) -> EvaluationRunRow:
    return EvaluationRunRow(
        id=r.id, dataset_id=r.dataset_id, experiment_id=r.experiment_id,
        experiment_run_id=r.experiment_run_id, strategy_id=r.strategy_id,
        strategy_version=r.strategy_version, pipeline_run_id=r.pipeline_run_id,
        status=r.status.value, result_json=dumps(r.result.to_dict()),
        error_message=r.error_message, created_at=r.created_at)


def _row_to_run(r: EvaluationRunRow) -> EvaluationRun:
    return EvaluationRun(
        id=r.id, dataset_id=r.dataset_id, experiment_id=r.experiment_id,
        experiment_run_id=r.experiment_run_id, strategy_id=r.strategy_id,
        strategy_version=r.strategy_version, pipeline_run_id=r.pipeline_run_id,
        status=EvaluationStatus(r.status), result=EvaluationResult.from_dict(loads(r.result_json)),
        error_message=r.error_message, created_at=r.created_at)


class EvaluationRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like users/strategies/experiments."""

    def save_dataset(self, d: EvaluationDataset) -> None:
        with get_session() as session:
            session.merge(_dataset_to_row(d))
            session.commit()

    def get_dataset(self, dataset_id: str) -> EvaluationDataset | None:
        with get_session() as session:
            row = session.get(EvaluationDatasetRow, dataset_id)
        return _row_to_dataset(row) if row else None

    def list_datasets(self) -> list[EvaluationDataset]:
        with get_session() as session:
            rows = session.exec(select(EvaluationDatasetRow).order_by(EvaluationDatasetRow.created_at.desc()))
            return [_row_to_dataset(r) for r in rows]

    def save_run(self, run: EvaluationRun) -> None:
        with get_session() as session:
            session.merge(_run_to_row(run))
            session.commit()

    def get_run(self, run_id: str) -> EvaluationRun | None:
        with get_session() as session:
            row = session.get(EvaluationRunRow, run_id)
        return _row_to_run(row) if row else None

    def list_runs(self, dataset_id: str = "", experiment_id: str = "") -> list[EvaluationRun]:
        """Oldest first."""
        stmt = select(EvaluationRunRow).order_by(EvaluationRunRow.created_at)
        if dataset_id:
            stmt = stmt.where(EvaluationRunRow.dataset_id == dataset_id)
        if experiment_id:
            stmt = stmt.where(EvaluationRunRow.experiment_id == experiment_id)
        with get_session() as session:
            return [_row_to_run(r) for r in session.exec(stmt)]

    def chunk_texts(self, pipeline_run_id: str, chunk_ids: Iterable[str]) -> dict[str, str]:
        """Full chunk text from the legacy chunks table (ExperimentRun.result only keeps text[:200])."""
        ids = list(set(chunk_ids))
        if not ids or not pipeline_run_id:
            return {}
        with get_session() as session:
            rows = session.exec(select(ChunkRow).where(ChunkRow.run_id == pipeline_run_id,
                                                       col(ChunkRow.id).in_(ids)))
            return {r.id: r.text for r in rows}
