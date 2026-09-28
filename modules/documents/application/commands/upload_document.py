from __future__ import annotations

from modules.documents.application.dto.document_dto import DocumentDTO
from modules.documents.application.services.document_service import DocumentService


class UploadDocumentCommand:
    """Register a file as a new document (version 1). Returns the DocumentDTO."""

    def __init__(self, service: DocumentService | None = None):
        self.service = service or DocumentService()

    def execute(self, name: str, filename: str, data: bytes, note: str = "",
                allow_duplicate: bool = False) -> DocumentDTO:
        return DocumentDTO.from_entity(self.service.upload(name, filename, data, note, allow_duplicate))
