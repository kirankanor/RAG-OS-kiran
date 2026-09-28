from __future__ import annotations

from modules.documents.application.dto.document_dto import DocumentDTO
from modules.documents.application.services.document_service import DocumentService


class DeleteDocumentCommand:
    """Soft-delete a document (idempotent). Its versions and files are kept."""

    def __init__(self, service: DocumentService | None = None):
        self.service = service or DocumentService()

    def execute(self, document_id: str) -> DocumentDTO:
        return DocumentDTO.from_entity(self.service.delete(document_id))
