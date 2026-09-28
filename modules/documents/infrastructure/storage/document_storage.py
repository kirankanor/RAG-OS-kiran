from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from modules.documents.domain.exceptions import DocumentStorageError
from shared.config.settings import get_settings


class DocumentBlobStore(ABC):
    """Stores the raw bytes of document versions. Distinct from the ingestion module's
    DocumentStorage (parsed CanonicalDocuments) and from shared local_file_store (per-run uploads)."""

    @abstractmethod
    def put(self, document_id: str, version: int, filename: str, data: bytes) -> str:
        """Store bytes, return an opaque storage key."""

    @abstractmethod
    def path(self, key: str) -> Path:
        """Local filesystem path of the stored file (what ingestion/experiments take as a file path)."""

    @abstractmethod
    def read(self, key: str) -> bytes: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...


class LocalDocumentBlobStore(DocumentBlobStore):
    """Layout: <data_dir>/documents/<document_id>/v<version>/<filename>."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else get_settings().data_dir / "documents"

    def put(self, document_id: str, version: int, filename: str, data: bytes) -> str:
        key = f"{document_id}/v{version}/{filename}"
        dest = self.path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key

    def path(self, key: str) -> Path:
        root = self.root.resolve()
        p = (root / key).resolve()
        if root not in p.parents:
            raise DocumentStorageError(f"Unsafe storage key '{key}'.")
        return p

    def read(self, key: str) -> bytes:
        p = self.path(key)
        if not p.is_file():
            raise DocumentStorageError(f"Stored file is missing: {key}")
        return p.read_bytes()

    def delete(self, key: str) -> None:
        p = self.path(key)
        p.unlink(missing_ok=True)
        try:
            p.parent.rmdir()  # only removes the version folder if empty
        except OSError:
            pass
