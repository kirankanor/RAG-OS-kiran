from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import select

from modules.experiments.domain.entities.experiment import Experiment
from modules.experiments.domain.entities.experiment_run import ExperimentRun
from modules.experiments.domain.models.experiment_config import ExperimentConfig, StrategyRef
from modules.experiments.domain.value_objects.experiment_id import ExperimentId
from modules.experiments.domain.value_objects.experiment_status import ExperimentStatus
from modules.experiments.infrastructure.persistence.models import ExperimentRow, ExperimentRunRow
from shared.infrastructure.database.db_models import dumps, get_session, loads


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _run_to_row(r: ExperimentRun) -> ExperimentRunRow:
    return ExperimentRunRow(
        id=r.id, experiment_id=r.experiment_id, position=r.position, strategy_id=r.strategy_id,
        strategy_version=r.strategy_version, status=r.status.value, pipeline_run_id=r.pipeline_run_id,
        result_json=dumps(r.result), error_message=r.error_message, started_at=r.started_at,
        finished_at=r.finished_at, duration_seconds=r.duration_seconds)


def _row_to_run(row: ExperimentRunRow) -> ExperimentRun:
    return ExperimentRun(
        id=row.id, experiment_id=row.experiment_id, position=row.position,
        strategy_id=row.strategy_id, strategy_version=row.strategy_version,
        status=ExperimentStatus(row.status), pipeline_run_id=row.pipeline_run_id,
        result=loads(row.result_json), error_message=row.error_message, started_at=row.started_at,
        finished_at=row.finished_at, duration_seconds=row.duration_seconds)


def _experiment_to_row(e: Experiment) -> ExperimentRow:
    return ExperimentRow(
        id=str(e.id), name=e.name, description=e.description, config_json=dumps(e.config.to_dict()),
        strategies_json=dumps([r.to_dict() for r in e.strategy_refs]), status=e.status.value,
        created_at=e.created_at, updated_at=e.updated_at, completed_at=e.completed_at)


def _load(session, row: ExperimentRow) -> Experiment:
    run_rows = session.exec(select(ExperimentRunRow).where(ExperimentRunRow.experiment_id == row.id)
                            .order_by(ExperimentRunRow.position))
    return Experiment(
        id=ExperimentId(row.id), name=row.name, description=row.description,
        config=ExperimentConfig.from_dict(loads(row.config_json)),
        strategy_refs=[StrategyRef.from_dict(d) for d in loads(row.strategies_json)],
        runs=[_row_to_run(r) for r in run_rows], status=ExperimentStatus(row.status),
        created_at=row.created_at, updated_at=row.updated_at, completed_at=row.completed_at)


class ExperimentRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like users/strategies."""

    def save(self, e: Experiment) -> None:
        with get_session() as session:
            session.merge(_experiment_to_row(e))
            for r in e.runs:
                session.merge(_run_to_row(r))
            session.commit()

    def save_run(self, run: ExperimentRun) -> None:
        with get_session() as session:
            session.merge(_run_to_row(run))
            session.commit()

    def get(self, experiment_id: str) -> Experiment | None:
        with get_session() as session:
            row = session.get(ExperimentRow, experiment_id)
            return _load(session, row) if row else None

    def list(self) -> list[Experiment]:
        with get_session() as session:
            rows = session.exec(select(ExperimentRow).order_by(ExperimentRow.created_at.desc()))
            return [_load(session, r) for r in rows]

    def get_runs(self, experiment_id: str) -> list[ExperimentRun]:
        with get_session() as session:
            rows = session.exec(select(ExperimentRunRow).where(
                ExperimentRunRow.experiment_id == experiment_id).order_by(ExperimentRunRow.position))
            return [_row_to_run(r) for r in rows]

    def get_status(self, experiment_id: str) -> ExperimentStatus | None:
        with get_session() as session:
            row = session.get(ExperimentRow, experiment_id)
            return ExperimentStatus(row.status) if row else None

    def set_status(self, experiment_id: str, status: ExperimentStatus) -> None:
        """Never overwrites CANCELLED with another status (stop may race with the orchestrator)."""
        with get_session() as session:
            row = session.get(ExperimentRow, experiment_id)
            if row is None or (row.status == ExperimentStatus.CANCELLED.value
                               and status != ExperimentStatus.CANCELLED):
                return
            row.status = status.value
            row.updated_at = _now()
            if status.is_terminal:
                row.completed_at = row.updated_at
            session.add(row)
            session.commit()

    def mark_cancelled(self, experiment_id: str) -> bool:
        """Cancel a non-terminal experiment and all its still-PENDING runs. Runs already
        RUNNING are left alone and finish normally."""
        with get_session() as session:
            row = session.get(ExperimentRow, experiment_id)
            if row is None or ExperimentStatus(row.status).is_terminal:
                return False
            row.status = ExperimentStatus.CANCELLED.value
            row.updated_at = row.completed_at = _now()
            session.add(row)
            pending = session.exec(select(ExperimentRunRow).where(
                ExperimentRunRow.experiment_id == experiment_id,
                ExperimentRunRow.status == ExperimentStatus.PENDING.value))
            for r in pending:
                r.status = ExperimentStatus.CANCELLED.value
                r.finished_at = row.updated_at
                session.add(r)
            session.commit()
            return True