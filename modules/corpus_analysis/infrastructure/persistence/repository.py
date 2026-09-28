from __future__ import annotations

from sqlmodel import select

from modules.corpus_analysis.domain.entities.analysis_run import AnalysisRun, AnalysisStatus
from modules.corpus_analysis.domain.entities.corpus_profile import CorpusProfile
from modules.corpus_analysis.infrastructure.persistence.models import AnalysisRunRow, CorpusProfileRow
from shared.infrastructure.database.db_models import dumps, get_session, loads


def _run_to_row(r: AnalysisRun) -> AnalysisRunRow:
    return AnalysisRunRow(id=r.id, name=r.name, sources_json=dumps(r.source_filenames),
                          status=r.status.value, error_message=r.error_message,
                          created_at=r.created_at, completed_at=r.completed_at)


def _row_to_run(row: AnalysisRunRow) -> AnalysisRun:
    return AnalysisRun(id=row.id, name=row.name, source_filenames=list(loads(row.sources_json) or []),
                       status=AnalysisStatus(row.status), error_message=row.error_message,
                       created_at=row.created_at, completed_at=row.completed_at)


def _profile_to_row(p: CorpusProfile) -> CorpusProfileRow:
    return CorpusProfileRow(id=p.id, analysis_run_id=p.analysis_run_id,
                            profile_json=dumps(p.to_dict()), created_at=p.created_at)


def _row_to_profile(row: CorpusProfileRow) -> CorpusProfile:
    return CorpusProfile.from_dict(loads(row.profile_json))


class CorpusAnalysisRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like users/strategies/experiments."""

    def save_run(self, run: AnalysisRun) -> None:
        with get_session() as session:
            session.merge(_run_to_row(run))
            session.commit()

    def get_run(self, run_id: str) -> AnalysisRun | None:
        with get_session() as session:
            row = session.get(AnalysisRunRow, run_id)
        return _row_to_run(row) if row else None

    def save_profile(self, profile: CorpusProfile) -> None:
        with get_session() as session:
            session.merge(_profile_to_row(profile))
            session.commit()

    def get_profile(self, profile_id: str) -> CorpusProfile | None:
        with get_session() as session:
            row = session.get(CorpusProfileRow, profile_id)
        return _row_to_profile(row) if row else None

    def get_profile_for_run(self, run_id: str) -> CorpusProfile | None:
        with get_session() as session:
            row = session.exec(select(CorpusProfileRow).where(
                CorpusProfileRow.analysis_run_id == run_id)).first()
        return _row_to_profile(row) if row else None

    def list_profiles(self) -> list[CorpusProfile]:
        """Newest first."""
        with get_session() as session:
            rows = session.exec(select(CorpusProfileRow).order_by(CorpusProfileRow.created_at.desc()))
            return [_row_to_profile(r) for r in rows]
