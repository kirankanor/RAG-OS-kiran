from __future__ import annotations

from dataclasses import replace

from modules.ingestion.application.dto.ingestion_dto import StartIngestionDTO
from modules.ingestion.application.services.ingestion_service import IngestionOutcome, IngestionService
from modules.ingestion.application.services.pipeline_runner import _params_hash
from modules.ingestion.infrastructure.parsers import parser_for_file


class ReprocessDocumentCommand:
    """Re-ingest one file with (possibly) new parser/chunker settings.

    If previous_document_id is given and its stored ProcessingVersion already
    matches the requested parser/chunker + params, nothing is done (returns
    None) unless force=True. Note the version does not capture file content,
    so use force=True if the file itself changed."""

    def __init__(self, service: IngestionService | None = None):
        self.service = service or IngestionService()

    def execute(self, file_path: str, dto: StartIngestionDTO, previous_document_id: str = "",
                force: bool = False) -> IngestionOutcome | None:
        dto = replace(dto, file_paths=[file_path])
        if previous_document_id and not force and self._is_up_to_date(file_path, dto, previous_document_id):
            return None
        return self.service.start(dto)

    def _is_up_to_date(self, file_path: str, dto: StartIngestionDTO, previous_document_id: str) -> bool:
        version = self.service.storage.load(previous_document_id).version
        if version is None:
            return False
        parser_name = (parser_for_file(file_path).name if dto.parser_name == "auto_by_extension"
                       else dto.parser_name)
        return version.matches_strategy(parser_name, _params_hash(dto.parser_params),
                                        dto.chunker_name, _params_hash(dto.chunker_params))
