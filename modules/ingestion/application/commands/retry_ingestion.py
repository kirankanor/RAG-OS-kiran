from __future__ import annotations

from modules.ingestion.application.dto.ingestion_dto import StartIngestionDTO
from modules.ingestion.application.services.ingestion_service import IngestionOutcome, IngestionService
from modules.ingestion.domain.exceptions import IngestionError


class RetryIngestionCommand:
    """Re-run the FAILED jobs of an existing run. dto.file_paths must include
    the failed files (matched by filename)."""

    def __init__(self, service: IngestionService | None = None):
        self.service = service or IngestionService()

    def execute(self, run_id: str, dto: StartIngestionDTO) -> IngestionOutcome:
        if not run_id:
            raise IngestionError("run_id is required.")
        return self.service.retry(run_id, dto)
