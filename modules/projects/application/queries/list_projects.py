from __future__ import annotations

from modules.projects.application.dto.project_dto import ProjectDTO
from modules.projects.application.services.project_service import ProjectService
from modules.projects.domain.value_objects.project_status import ProjectStatus


class ListProjectsQuery:
    """Newest first. owner_id="" lists everyone's projects."""

    def __init__(self, service: ProjectService | None = None):
        self.service = service or ProjectService()

    def execute(self, owner_id: str = "", include_archived: bool = True,
                include_deleted: bool = False) -> list[ProjectDTO]:
        statuses = [ProjectStatus.ACTIVE]
        if include_archived:
            statuses.append(ProjectStatus.ARCHIVED)
        if include_deleted:
            statuses.append(ProjectStatus.DELETED)
        return [ProjectDTO.from_entity(p) for p in self.service.list(owner_id, statuses)]
