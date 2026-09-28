from __future__ import annotations

from pathlib import Path

from modules.documents.application.dto.document_dto import DocumentDTO, DocumentVersionDTO
from modules.documents.application.services.document_service import DocumentService


class GetDocumentQuery:
    def __init__(self, service: DocumentService | None = None):
        self.service = service or DocumentService()

    def execute(self, document_id: str) -> DocumentDTO:
        return DocumentDTO.from_entity(self.service.get(document_id))

    def version(self, document_id: str, number: int | None = None) -> DocumentVersionDTO:
        return DocumentVersionDTO.from_entity(self.service.get_version(document_id, number))

    def file_path(self, document_id: str, number: int | None = None) -> Path:
        """Local path of a stored version (current if number is None), ready to pass to ingestion."""
        return self.service.file_path(document_id, number)
