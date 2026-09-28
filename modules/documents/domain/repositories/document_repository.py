from __future__ import annotations

from abc import ABC, abstractmethod

from modules.documents.domain.entities.document import Document


class DocumentRepository(ABC):
    """Port for persisting Document aggregates (with their versions)."""

    @abstractmethod
    def save(self, document: Document) -> None:
        """Insert or update. Versions are append-only: existing ones are never rewritten."""

    @abstractmethod
    def get(self, document_id: str) -> Document | None:
        """Returns the document even if soft-deleted."""

    @abstractmethod
    def list(self, include_deleted: bool = False) -> list[Document]:
        """Newest first."""

    @abstractmethod
    def find_by_content_hash(self, content_hash: str, include_deleted: bool = False) -> list[Document]:
        """Documents having ANY version with this hash (callers filter on the current version if needed)."""
