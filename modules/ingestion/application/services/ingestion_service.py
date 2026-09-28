from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import SQLModel

from modules.ingestion.application.dto.ingestion_dto import IngestionRunDTO, StartIngestionDTO
from modules.ingestion.application.services.pipeline_runner import PipelineRunner
from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.entities.ingestion_run import IngestionRun
from modules.ingestion.domain.exceptions import IngestionError, IngestionJobFailedError
from modules.ingestion.domain.interfaces.storage import DocumentStorage, document_storage_registry
from modules.ingestion.domain.value_objects.ingestion_status import IngestionStatus
# Importing models registers the 3 ingestion tables on SQLModel.metadata.
from modules.ingestion.infrastructure.persistence import models as _models  # noqa: F401
from modules.ingestion.infrastructure.persistence import repository
from shared.domain.types import Chunk
from shared.infrastructure.database.db_models import get_engine


def _ensure_tables() -> None:
    """create_all is idempotent and creates any missing tables even if the
    engine already exists, so this fixes the 'models imported too late' gap."""
    SQLModel.metadata.create_all(get_engine())


@dataclass
class IngestionOutcome:
    run: IngestionRunDTO
    documents: list[CanonicalDocument]
    chunks: list[Chunk]


class IngestionService:
    """Application façade: creates runs/jobs, drives PipelineRunner per file,
    and persists progress after every job."""

    def __init__(self, storage: DocumentStorage | None = None):
        _ensure_tables()
        self.storage = storage or document_storage_registry.create("sql")

    def start(self, dto: StartIngestionDTO) -> IngestionOutcome:
        runner = PipelineRunner(dto, storage=self.storage)  # fail fast on bad config, before any state is written
        run = IngestionRun(name=dto.run_name)
        pairs: list[tuple[IngestionJob, str]] = []
        for fp in dto.file_paths:
            job = IngestionJob(source_filename=Path(fp).name)
            run.add_job(job)
            pairs.append((job, str(fp)))
        repository.save_run(run)
        return self._execute(run, pairs, runner)

    def retry(self, run_id: str, dto: StartIngestionDTO) -> IngestionOutcome:
        """Re-run FAILED jobs of an existing run. dto.file_paths must include
        the failed files (matched by filename); dto config is used for the retry."""
        runner = PipelineRunner(dto, storage=self.storage)
        run = repository.get_run(run_id)
        if run is None:
            raise IngestionError(f"No ingestion run found with id '{run_id}'")
        paths = {Path(fp).name: str(fp) for fp in dto.file_paths}
        pairs = []
        for job in run.jobs:
            if job.status == IngestionStatus.FAILED and job.source_filename in paths:
                job.retry()
                pairs.append((job, paths[job.source_filename]))
        return self._execute(run, pairs, runner)

    def get_run(self, run_id: str) -> IngestionRunDTO | None:
        run = repository.get_run(run_id)
        return IngestionRunDTO.from_entity(run) if run else None

    def _execute(self, run: IngestionRun, pairs: list[tuple[IngestionJob, str]],
                 runner: PipelineRunner) -> IngestionOutcome:
        documents: list[CanonicalDocument] = []
        chunks: list[Chunk] = []
        for job, path in pairs:
            job.start()
            try:
                result = runner.process(job, path)
            except IngestionJobFailedError as e:
                job.fail(str(e))
            else:
                job.complete()
                documents.append(result.canonical)
                chunks.extend(result.chunks)
            repository.update_job(job)
        if run.status.is_terminal:
            run.mark_completed()
        repository.save_run(run)
        return IngestionOutcome(run=IngestionRunDTO.from_entity(run), documents=documents, chunks=chunks)
