from __future__ import annotations

from modules.ingestion.application.dto.ingestion_dto import StartIngestionDTO
from modules.ingestion.application.services.ingestion_service import IngestionOutcome, IngestionService
from modules.ingestion.domain.exceptions import IngestionError


class StartIngestionCommand:
    """Start a new ingestion run over one or more files."""

    def __init__(self, service: IngestionService | None = None):
        self.service = service or IngestionService()

    def execute(self, dto: StartIngestionDTO) -> IngestionOutcome:
        if not dto.file_paths:
            raise IngestionError("No file paths provided.")
        return self.service.start(dto)
