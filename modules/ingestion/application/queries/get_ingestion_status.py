from __future__ import annotations

from modules.ingestion.application.dto.ingestion_dto import IngestionRunDTO
from modules.ingestion.application.services.ingestion_service import IngestionService
from modules.ingestion.domain.exceptions import IngestionError


class GetIngestionStatusQuery:
    """Fetch an ingestion run (with per-job status/stage) by id."""

    def __init__(self, service: IngestionService | None = None):
        self.service = service or IngestionService()

    def execute(self, run_id: str) -> IngestionRunDTO:
        run = self.service.get_run(run_id)
        if run is None:
            raise IngestionError(f"No ingestion run found with id '{run_id}'")
        return run
