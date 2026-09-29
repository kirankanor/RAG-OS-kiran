from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.artifacts.domain.exceptions import ArtifactStorageError
from shared.config.settings import get_settings


class ArtifactBlobStore(ABC):
    """Stores the bytes of generated artifacts."""

    @abstractmethod
    def put(self, artifact_id: str, filename: str, data: bytes) -> str:
        """Store bytes, return an opaque storage key."""

    @abstractmethod
    def path(self, key: str) -> Path: ...

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalArtifactBlobStore(ArtifactBlobStore):
    """Layout: <data_dir>/artifacts/<artifact_id>/<filename>."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else get_settings().data_dir / "artifacts"

    def put(self, artifact_id: str, filename: str, data: bytes) -> str:
        key = f"{artifact_id}/{filename}"
        dest = self.path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key

    def path(self, key: str) -> Path:
        root = self.root.resolve()
        p = (root / key).resolve()
        if root not in p.parents:
            raise ArtifactStorageError(f"Unsafe storage key '{key}'.")
        return p

    def read(self, key: str) -> bytes:
        p = self.path(key)
        if not p.is_file():
            raise ArtifactStorageError(f"Stored file is missing: {key}")
        return p.read_bytes()

    def delete(self, key: str) -> None:
        p = self.path(key)
        p.unlink(missing_ok=True)
        try:
            p.parent.rmdir()
        except OSError:
            pass
