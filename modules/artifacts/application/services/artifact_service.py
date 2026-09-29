from __future__ import annotations

import hashlib
import re
from pathlib import Path

from sqlmodel import SQLModel

from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.exceptions import (
    ArtifactGenerationError, ArtifactNotFoundError, ArtifactStorageError, InvalidArtifactError,
)
from modules.artifacts.domain.value_objects.artifact_status import ArtifactStatus
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
# Importing models registers the artifacts table on SQLModel.metadata.
from modules.artifacts.infrastructure.persistence import models as _models  # noqa: F401
from modules.artifacts.infrastructure.persistence.repository import ArtifactRepository
from modules.artifacts.infrastructure.storage.artifact_storage import (
    ArtifactBlobStore, LocalArtifactBlobStore,
)
from shared.infrastructure.database.db_models import get_engine

_PATH_SPLIT_RE = re.compile(r"[\\/]")


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class ArtifactService:
    """Records generated files (bytes in the blob store, metadata in the DB) and reads them back.
    The generation services (report/code/package) call `record()`."""

    def __init__(self, repository: ArtifactRepository | None = None,
                 blobs: ArtifactBlobStore | None = None):
        _ensure_tables()
        self.repository = repository or ArtifactRepository()
        self.blobs = blobs or LocalArtifactBlobStore()

    def record(self, artifact_type: ArtifactType, name: str, filename: str, data: bytes,
               source_type: str = "", source_id: str = "", note: str = "") -> Artifact:
        filename = _PATH_SPLIT_RE.split(filename.strip())[-1].strip()
        if filename in ("", ".", ".."):
            raise InvalidArtifactError("A filename is required.")
        if not data:
            raise InvalidArtifactError("Generated content is empty.")
        artifact = Artifact(type=artifact_type, name=name.strip() or filename, source_type=source_type,
                            source_id=source_id, filename=filename, note=note)
        try:
            key = self.blobs.put(artifact.id, filename, data)
        except Exception as e:  # noqa: BLE001
            artifact.fail(f"{type(e).__name__}: {e}")
            self.repository.save(artifact)
            raise ArtifactGenerationError(f"Could not store artifact: {e}") from e
        artifact.complete(key, len(data), hashlib.sha256(data).hexdigest())
        try:
            self.repository.save(artifact)
        except Exception:
            self.blobs.delete(key)  # don't leave an orphan file behind
            raise
        return artifact

    def get(self, artifact_id: str) -> Artifact:
        a = self.repository.get(artifact_id)
        if a is None:
            raise ArtifactNotFoundError(f"No artifact with id '{artifact_id}'")
        return a

    def list(self, source_type: str = "", source_id: str = "",
             artifact_type: ArtifactType | None = None) -> list[Artifact]:
        return self.repository.list(source_type, source_id, artifact_type)

    def file_path(self, artifact_id: str) -> Path:
        a = self.get(artifact_id)
        if a.status != ArtifactStatus.COMPLETED or not a.storage_key:
            raise ArtifactStorageError(f"Artifact '{artifact_id}' has no stored file.")
        path = self.blobs.path(a.storage_key)
        if not path.is_file():
            raise ArtifactStorageError(f"Stored file is missing: {path}")
        return path

    def read_bytes(self, artifact_id: str) -> bytes:
        return self.file_path(artifact_id).read_bytes()
