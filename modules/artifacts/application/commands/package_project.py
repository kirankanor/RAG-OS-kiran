from __future__ import annotations

from modules.artifacts.application.services.package_service import PackageService
from modules.artifacts.domain.entities.artifact import Artifact


class PackageProjectCommand:
    """Zip a project's experiments, decision reports and strategy scripts (and optionally its documents)."""

    def __init__(self, service: PackageService | None = None):
        self.service = service or PackageService()

    def execute(self, project_id: str, include_documents: bool = False) -> Artifact:
        return self.service.package_project(project_id, include_documents)
