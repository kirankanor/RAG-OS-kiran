from __future__ import annotations

from modules.documents.application.dto.document_dto import DocumentDTO
from modules.documents.application.services.document_service import DocumentService


class CreateVersionCommand:
    """Add a new version of an existing document. Raises UnchangedContentError if the content is identical."""

    def __init__(self, service: DocumentService | None = None):
        self.service = service or DocumentService()

    def execute(self, document_id: str, data: bytes, filename: str = "", note: str = "") -> DocumentDTO:
        return DocumentDTO.from_entity(self.service.create_version(document_id, data, filename, note))
