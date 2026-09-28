from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from modules.projects.domain.entities.project import Project
from modules.projects.domain.value_objects.project_status import ProjectStatus


class ProjectRepository(ABC):
    """Port for persisting Project aggregates."""

    @abstractmethod
    def save(self, project: Project) -> None:
        """Insert or update."""

    @abstractmethod
    def get(self, project_id: str) -> Project | None:
        """Returns the project even if soft-deleted."""

    @abstractmethod
    def list(self, owner_id: str = "", statuses: Iterable[ProjectStatus] | None = None) -> list[Project]:
        """Newest first. statuses=None means active and archived (not deleted)."""
