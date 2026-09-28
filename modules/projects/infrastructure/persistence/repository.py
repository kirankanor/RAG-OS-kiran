from __future__ import annotations

from collections.abc import Iterable

from sqlmodel import col, select

from modules.projects.domain.entities.project import Project
from modules.projects.domain.repositories.project_repository import ProjectRepository
from modules.projects.domain.value_objects.project_status import ProjectStatus
from modules.projects.infrastructure.mappers import project_to_row, row_to_project
from modules.projects.infrastructure.persistence.models import ProjectRow
from shared.infrastructure.database.db_models import get_session

_DEFAULT_STATUSES = (ProjectStatus.ACTIVE, ProjectStatus.ARCHIVED)


class SqlProjectRepository(ProjectRepository):
    """SQLModel implementation of the ProjectRepository port."""

    def save(self, project: Project) -> None:
        with get_session() as session:
            session.merge(project_to_row(project))
            session.commit()

    def get(self, project_id: str) -> Project | None:
        with get_session() as session:
            row = session.get(ProjectRow, project_id)
        return row_to_project(row) if row else None

    def list(self, owner_id: str = "", statuses: Iterable[ProjectStatus] | None = None) -> list[Project]:
        wanted = [s.value for s in (statuses if statuses is not None else _DEFAULT_STATUSES)]
        stmt = select(ProjectRow).where(col(ProjectRow.status).in_(wanted)).order_by(
            ProjectRow.created_at.desc())
        if owner_id:
            stmt = stmt.where(ProjectRow.owner_id == owner_id)
        with get_session() as session:
            return [row_to_project(r) for r in session.exec(stmt)]
