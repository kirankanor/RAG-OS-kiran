from __future__ import annotations

from modules.projects.application.dto.project_dto import ProjectDTO
from modules.projects.application.services.project_service import ProjectService


class DeleteProjectCommand:
    """Soft-delete a project (idempotent). Its documents and experiments are not touched."""

    def __init__(self, service: ProjectService | None = None):
        self.service = service or ProjectService()

    def execute(self, project_id: str) -> ProjectDTO:
        return ProjectDTO.from_entity(self.service.delete(project_id))
