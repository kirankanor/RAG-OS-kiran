from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from sqlmodel import SQLModel

from modules.documents.domain.entities.document import Document
from modules.documents.domain.entities.document_version import DocumentVersion
from modules.documents.domain.events.document_events import DocumentEvent
from modules.documents.domain.exceptions import (
    DocumentNotFoundError, DocumentStateError, DocumentStorageError, DocumentVersionNotFoundError,
    DuplicateDocumentError, InvalidDocumentError, UnchangedContentError, UnsupportedDocumentTypeError,
)
from modules.documents.domain.repositories.document_repository import DocumentRepository
from modules.documents.domain.value_objects.document_hash import DocumentHash
from modules.documents.infrastructure.persistence import models as _models  # noqa: F401  (registers tables)
from modules.documents.infrastructure.persistence.repository import SqlDocumentRepository
from modules.documents.infrastructure.storage.document_storage import DocumentBlobStore, LocalDocumentBlobStore
from modules.ingestion.infrastructure.parsers.base import DEFAULT_STRATEGY_BY_EXTENSION
from shared.infrastructure.database.db_models import get_engine

DEFAULT_MAX_SIZE_BYTES = 50 * 1024 * 1024  # same limit as ingestion's FileValidator
_PATH_SPLIT_RE = re.compile(r"[\\/]")

EventPublisher = Callable[[DocumentEvent], None]


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


class DocumentService:
    """Document registry: stores file bytes as immutable, hashed versions and tracks the
    lifecycle (upload, new version, soft delete). It never parses; other modules refer to
    a document by id and get a local file path from `file_path()` to feed ingestion.
    Events are handed to `publisher` (if any) after the change is saved."""

    def __init__(self, repository: DocumentRepository | None = None, blobs: DocumentBlobStore | None = None,
                 publisher: EventPublisher | None = None, max_size_bytes: int = DEFAULT_MAX_SIZE_BYTES):
        _ensure_tables()
        self.repository = repository or SqlDocumentRepository()
        self.blobs = blobs or LocalDocumentBlobStore()
        self.publisher = publisher
        self.max_size_bytes = max_size_bytes

    # --- commands -----------------------------------------------------------

    def upload(self, name: str, filename: str, data: bytes, note: str = "",
               allow_duplicate: bool = False) -> Document:
        """Create a document with version 1. Rejects content that is already the current
        version of an active document unless allow_duplicate=True."""
        filename = self._clean_filename(filename)
        self._validate_file(filename, data)
        content_hash = DocumentHash.from_bytes(data)
        if not allow_duplicate:
            for existing in self.repository.find_by_content_hash(content_hash.value):
                if existing.current_version and existing.current_version.content_hash == content_hash:
                    raise DuplicateDocumentError(
                        f"Identical content is already the current version of document '{existing.id}' "
                        f"({existing.name}).", str(existing.id))
        document = Document(name=name.strip() or filename)
        self._store_version(document, filename, data, content_hash, note)
        return document

    def create_version(self, document_id: str, data: bytes, filename: str = "", note: str = "") -> Document:
        """Append a new version. Raises UnchangedContentError if the bytes equal the current version."""
        document = self.get(document_id)
        if document.is_deleted:
            raise DocumentStateError(f"Document '{document_id}' is deleted.")
        filename = self._clean_filename(filename or document.filename)
        self._validate_file(filename, data)
        content_hash = DocumentHash.from_bytes(data)
        if document.current_version and document.current_version.content_hash == content_hash:
            raise UnchangedContentError(
                f"Content is identical to version {document.current_version.number} of '{document_id}'.")
        self._store_version(document, filename, data, content_hash, note)
        return document

    def delete(self, document_id: str) -> Document:
        """Soft delete (idempotent). Versions and files are kept."""
        document = self.get(document_id)
        if document.delete():
            self.repository.save(document)
            self._publish(document)
        return document

    # --- queries ------------------------------------------------------------

    def get(self, document_id: str) -> Document:
        d = self.repository.get(document_id)
        if d is None:
            raise DocumentNotFoundError(f"No document with id '{document_id}'")
        return d

    def list(self, include_deleted: bool = False) -> list[Document]:
        return self.repository.list(include_deleted)

    def get_version(self, document_id: str, number: int | None = None) -> DocumentVersion:
        """`number=None` means the current version."""
        document = self.get(document_id)
        version = document.current_version if number is None else document.version(number)
        if version is None:
            raise DocumentVersionNotFoundError(f"Document '{document_id}' has no version {number}")
        return version

    def file_path(self, document_id: str, number: int | None = None) -> Path:
        """Local path of a stored version. Pass it wherever a file path is expected (ingestion, experiments)."""
        path = self.blobs.path(self.get_version(document_id, number).storage_key)
        if not path.is_file():
            raise DocumentStorageError(f"Stored file is missing: {path}")
        return path

    def read_bytes(self, document_id: str, number: int | None = None) -> bytes:
        return self.blobs.read(self.get_version(document_id, number).storage_key)

    # --- internals ----------------------------------------------------------

    def _store_version(self, document: Document, filename: str, data: bytes, content_hash: DocumentHash,
                       note: str) -> None:
        number = len(document.versions) + 1
        key = self.blobs.put(str(document.id), number, filename, data)
        try:
            document.add_version(DocumentVersion(number=number, content_hash=content_hash,
                                                 size_bytes=len(data), filename=filename,
                                                 storage_key=key, note=note))
            self.repository.save(document)
        except Exception:
            self.blobs.delete(key)  # don't leave an orphan file behind
            raise
        self._publish(document)

    def _publish(self, document: Document) -> None:
        events = document.pull_events()
        if self.publisher:
            for event in events:
                self.publisher(event)

    def _clean_filename(self, filename: str) -> str:
        name = _PATH_SPLIT_RE.split(filename.strip())[-1].strip()
        if name in ("", ".", ".."):
            raise InvalidDocumentError("A filename is required.")
        return name

    def _validate_file(self, filename: str, data: bytes) -> None:
        ext = Path(filename).suffix.lower()
        if ext not in DEFAULT_STRATEGY_BY_EXTENSION:
            raise UnsupportedDocumentTypeError(f"Unsupported file extension: '{ext}'")
        if not data:
            raise InvalidDocumentError("File is empty.")
        if len(data) > self.max_size_bytes:
            raise InvalidDocumentError(
                f"File exceeds max size of {self.max_size_bytes} bytes ({len(data)} bytes).")
