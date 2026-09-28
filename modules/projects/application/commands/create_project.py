from __future__ import annotations

from collections.abc import Iterable

from modules.projects.application.dto.project_dto import ProjectDTO
from modules.projects.application.services.project_service import ProjectService


class CreateProjectCommand:
    """Create a project for an existing, active user, optionally linking documents and experiments by id."""

    def __init__(self, service: ProjectService | None = None):
        self.service = service or ProjectService()

    def execute(self, name: str, owner_id: str, description: str = "", document_ids: Iterable[str] = (),
                experiment_ids: Iterable[str] = ()) -> ProjectDTO:
        return ProjectDTO.from_entity(
            self.service.create(name, owner_id, description, document_ids, experiment_ids))
