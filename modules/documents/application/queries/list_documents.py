from __future__ import annotations

from modules.documents.application.dto.document_dto import DocumentDTO
from modules.documents.application.services.document_service import DocumentService


class ListDocumentsQuery:
    def __init__(self, service: DocumentService | None = None):
        self.service = service or DocumentService()

    def execute(self, include_deleted: bool = False) -> list[DocumentDTO]:
        return [DocumentDTO.from_entity(d) for d in self.service.list(include_deleted)]
