from __future__ import annotations

from abc import ABC, abstractmethod

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from shared.domain.registry import Registry


class DocumentStorage(ABC):
    """Port for persisting/retrieving CanonicalDocument objects, independent
    of the backing store (local disk, DB, S3, ...).

    Distinct from shared.infrastructure.storage.local_file_store, which only
    handles raw uploaded file bytes, not the structured post-parsing
    representation.
    """

    name: str = "base"

    @abstractmethod
    def save(self, document: CanonicalDocument) -> str:
        """Persist the document, returning its storage key/id."""
        raise NotImplementedError

    @abstractmethod
    def load(self, document_id: str) -> CanonicalDocument:
        raise NotImplementedError

    @abstractmethod
    def exists(self, document_id: str) -> bool:
        raise NotImplementedError


document_storage_registry: Registry[DocumentStorage] = Registry("document_storage")
