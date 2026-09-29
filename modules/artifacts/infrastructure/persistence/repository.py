from __future__ import annotations

from sqlmodel import select

from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.value_objects.artifact_status import ArtifactStatus
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
from modules.artifacts.infrastructure.persistence.models import ArtifactRow
from shared.infrastructure.database.db_models import get_session


def _to_row(a: Artifact) -> ArtifactRow:
    return ArtifactRow(id=a.id, type=a.type.value, name=a.name, source_type=a.source_type,
                       source_id=a.source_id, status=a.status.value, filename=a.filename,
                       storage_key=a.storage_key, size_bytes=a.size_bytes, content_hash=a.content_hash,
                       note=a.note, error_message=a.error_message, created_at=a.created_at,
                       completed_at=a.completed_at)


def _from_row(r: ArtifactRow) -> Artifact:
    return Artifact(id=r.id, type=ArtifactType(r.type), name=r.name, source_type=r.source_type,
                    source_id=r.source_id, status=ArtifactStatus(r.status), filename=r.filename,
                    storage_key=r.storage_key, size_bytes=r.size_bytes, content_hash=r.content_hash,
                    note=r.note, error_message=r.error_message, created_at=r.created_at,
                    completed_at=r.completed_at)


class ArtifactRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like strategies/decisions."""

    def save(self, artifact: Artifact) -> None:
        with get_session() as session:
            session.merge(_to_row(artifact))
            session.commit()

    def get(self, artifact_id: str) -> Artifact | None:
        with get_session() as session:
            row = session.get(ArtifactRow, artifact_id)
        return _from_row(row) if row else None

    def list(self, source_type: str = "", source_id: str = "",
             artifact_type: ArtifactType | None = None) -> list[Artifact]:
        """Newest first."""
        stmt = select(ArtifactRow).order_by(ArtifactRow.created_at.desc())
        if source_type:
            stmt = stmt.where(ArtifactRow.source_type == source_type)
        if source_id:
            stmt = stmt.where(ArtifactRow.source_id == source_id)
        if artifact_type is not None:
            stmt = stmt.where(ArtifactRow.type == artifact_type.value)
        with get_session() as session:
            return [_from_row(r) for r in session.exec(stmt)]
