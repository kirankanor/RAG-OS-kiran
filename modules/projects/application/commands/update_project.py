from __future__ import annotations

from collections.abc import Sequence

from modules.projects.application.dto.project_dto import ProjectDTO
from modules.projects.application.services.project_service import ProjectService


class UpdateProjectCommand:
    """Rename/redescribe a project, add or remove linked documents/experiments, and archive
    (archived=True) or unarchive (archived=False) it. Archived projects are read-only, so
    unarchive and edit in the same call. Fields left at their default are not touched."""

    def __init__(self, service: ProjectService | None = None):
        self.service = service or ProjectService()

    def execute(self, project_id: str, name: str | None = None, description: str | None = None,
                add_document_ids: Sequence[str] = (), remove_document_ids: Sequence[str] = (),
                add_experiment_ids: Sequence[str] = (), remove_experiment_ids: Sequence[str] = (),
                archived: bool | None = None) -> ProjectDTO:
        return ProjectDTO.from_entity(self.service.update(
            project_id, name, description, add_document_ids, remove_document_ids,
            add_experiment_ids, remove_experiment_ids, archived))
