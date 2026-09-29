from __future__ import annotations

from pathlib import Path

from modules.artifacts.application.services.artifact_service import ArtifactService
from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType


class ListArtifactsQuery:
    """Newest first. Empty filters list everything."""

    def __init__(self, service: ArtifactService | None = None):
        self.service = service or ArtifactService()

    def execute(self, source_type: str = "", source_id: str = "",
                artifact_type: ArtifactType | None = None) -> list[Artifact]:
        return self.service.list(source_type, source_id, artifact_type)

    def get(self, artifact_id: str) -> Artifact:
        return self.service.get(artifact_id)

    def file_path(self, artifact_id: str) -> Path:
        """Local path of the generated file, ready to serve or copy."""
        return self.service.file_path(artifact_id)
