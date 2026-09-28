from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.entities.ingestion_run import IngestionRun


@dataclass
class StartIngestionDTO:
    """Input for starting an ingestion run over one or more source files."""

    file_paths: list[str] = field(default_factory=list)
    run_name: str = ""
    parser_name: str = "auto_by_extension"
    parser_params: dict[str, Any] = field(default_factory=dict)
    chunker_name: str = "recursive_char"
    chunker_params: dict[str, Any] = field(default_factory=dict)
    validators: list[str] = field(default_factory=lambda: ["file_validator", "extraction_validator"])
    normalizers: list[str] = field(default_factory=lambda: ["text_normalizer", "structure_normalizer"])
    ocr_engine: str = ""  # empty = OCR disabled


@dataclass
class IngestionJobDTO:
    id: str = ""
    run_id: str = ""
    source_filename: str = ""
    status: str = ""
    stage: str = ""
    error_message: str = ""
    retry_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_entity(cls, job: IngestionJob) -> IngestionJobDTO:
        return cls(id=job.id, run_id=job.run_id, source_filename=job.source_filename,
                   status=job.status.value, stage=job.stage.value,
                   error_message=job.error_message, retry_count=job.retry_count,
                   created_at=job.created_at, updated_at=job.updated_at)


@dataclass
class IngestionRunDTO:
    id: str = ""
    name: str = ""
    status: str = ""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    jobs: list[IngestionJobDTO] = field(default_factory=list)
    created_at: str = ""
    completed_at: str = ""

    @classmethod
    def from_entity(cls, run: IngestionRun) -> IngestionRunDTO:
        jobs = [IngestionJobDTO.from_entity(j) for j in run.jobs]
        return cls(id=run.id, name=run.name, status=run.status.value,
                   total_jobs=len(jobs),
                   completed_jobs=sum(1 for j in jobs if j.status == "completed"),
                   failed_jobs=sum(1 for j in jobs if j.status == "failed"),
                   jobs=jobs, created_at=run.created_at, completed_at=run.completed_at)