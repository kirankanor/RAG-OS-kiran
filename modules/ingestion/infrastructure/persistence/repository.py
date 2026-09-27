from __future__ import annotations

from sqlmodel import select

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.entities.ingestion_run import IngestionRun
from modules.ingestion.domain.exceptions import DocumentNotFoundError
from modules.ingestion.domain.interfaces.storage import DocumentStorage, document_storage_registry
from modules.ingestion.domain.models.document_block import BlockType, DocumentBlock
from modules.ingestion.domain.models.figure import Figure
from modules.ingestion.domain.models.page import Page
from modules.ingestion.domain.models.table import Table
from modules.ingestion.domain.value_objects.ingestion_status import IngestionStatus
from modules.ingestion.domain.value_objects.processing_stage import ProcessingStage
from modules.ingestion.domain.value_objects.processing_version import ProcessingVersion
from modules.ingestion.infrastructure.persistence.models import (
    CanonicalDocumentRow, IngestionJobRow, IngestionRunRow,
)
from shared.infrastructure.database.db_models import dumps, get_session, loads

# --- CanonicalDocument <-> row serialization (manual, not dataclasses.asdict,
# so bbox round-trips as a tuple and enums round-trip as their proper types) --


def _tuple_or_none(value):
    return tuple(value) if value is not None else None


def _table_to_dict(table: Table) -> dict:
    return {"rows": table.rows, "caption": table.caption, "page_number": table.page_number, "bbox": table.bbox}


def _dict_to_table(data: dict) -> Table:
    return Table(rows=data.get("rows", []), caption=data.get("caption", ""),
                 page_number=data.get("page_number", 0), bbox=_tuple_or_none(data.get("bbox")))


def _figure_to_dict(figure: Figure) -> dict:
    return {"caption": figure.caption, "page_number": figure.page_number, "bbox": figure.bbox,
            "image_path": figure.image_path, "ocr_text": figure.ocr_text}


def _dict_to_figure(data: dict) -> Figure:
    return Figure(caption=data.get("caption", ""), page_number=data.get("page_number", 0),
                  bbox=_tuple_or_none(data.get("bbox")), image_path=data.get("image_path", ""),
                  ocr_text=data.get("ocr_text", ""))


def _block_to_dict(block: DocumentBlock) -> dict:
    return {
        "block_type": block.block_type.value, "text": block.text, "position": block.position,
        "page_number": block.page_number, "heading_level": block.heading_level, "bbox": block.bbox,
        "table": _table_to_dict(block.table) if block.table else None,
        "figure": _figure_to_dict(block.figure) if block.figure else None,
    }


def _dict_to_block(data: dict) -> DocumentBlock:
    return DocumentBlock(
        block_type=BlockType(data.get("block_type", "text")), text=data.get("text", ""),
        position=data.get("position", 0), page_number=data.get("page_number", 0),
        heading_level=data.get("heading_level", 0), bbox=_tuple_or_none(data.get("bbox")),
        table=_dict_to_table(data["table"]) if data.get("table") else None,
        figure=_dict_to_figure(data["figure"]) if data.get("figure") else None,
    )


def _page_to_dict(page: Page) -> dict:
    return {"page_number": page.page_number, "width": page.width, "height": page.height,
            "blocks": [_block_to_dict(b) for b in page.blocks]}


def _dict_to_page(data: dict) -> Page:
    return Page(page_number=data.get("page_number", 0), width=data.get("width", 0.0),
                height=data.get("height", 0.0),
                blocks=[_dict_to_block(b) for b in data.get("blocks", [])])


def _version_to_dict(version: ProcessingVersion | None) -> dict:
    if version is None:
        return {}
    return {"parser_name": version.parser_name, "parser_params_hash": version.parser_params_hash,
            "chunker_name": version.chunker_name, "chunker_params_hash": version.chunker_params_hash,
            "revision": version.revision}


def _dict_to_version(data: dict) -> ProcessingVersion | None:
    return ProcessingVersion(**data) if data else None


def _document_to_row(document: CanonicalDocument) -> CanonicalDocumentRow:
    return CanonicalDocumentRow(
        id=document.id, source_document_id=document.source_document_id,
        source_filename=document.source_filename,
        pages_json=dumps([_page_to_dict(p) for p in document.pages]),
        stage=document.stage.value, version_json=dumps(_version_to_dict(document.version)),
        created_at=document.created_at,
    )


def _row_to_document(row: CanonicalDocumentRow) -> CanonicalDocument:
    return CanonicalDocument(
        id=row.id, source_document_id=row.source_document_id, source_filename=row.source_filename,
        pages=[_dict_to_page(p) for p in loads(row.pages_json)],
        stage=ProcessingStage(row.stage), version=_dict_to_version(loads(row.version_json)),
        created_at=row.created_at,
    )


@document_storage_registry.register("sql", "Persists CanonicalDocument objects to the app's SQLite/SQLModel database.")
class SqlDocumentStorage(DocumentStorage):
    name = "sql"

    def save(self, document: CanonicalDocument) -> str:
        with get_session() as session:
            session.merge(_document_to_row(document))
            session.commit()
        return document.id

    def load(self, document_id: str) -> CanonicalDocument:
        with get_session() as session:
            row = session.get(CanonicalDocumentRow, document_id)
        if row is None:
            raise DocumentNotFoundError(f"No CanonicalDocument found with id '{document_id}'")
        return _row_to_document(row)

    def exists(self, document_id: str) -> bool:
        with get_session() as session:
            return session.get(CanonicalDocumentRow, document_id) is not None


# --- IngestionRun / IngestionJob persistence (plain functions, not behind
# a domain port -- these are ingestion-progress-tracking, not document storage) --


def _job_to_row(job: IngestionJob) -> IngestionJobRow:
    return IngestionJobRow(id=job.id, run_id=job.run_id, source_filename=job.source_filename,
                            status=job.status.value, stage=job.stage.value,
                            error_message=job.error_message, retry_count=job.retry_count,
                            created_at=job.created_at, updated_at=job.updated_at)


def _row_to_job(row: IngestionJobRow) -> IngestionJob:
    return IngestionJob(id=row.id, run_id=row.run_id, source_filename=row.source_filename,
                         status=IngestionStatus(row.status), stage=ProcessingStage(row.stage),
                         error_message=row.error_message, retry_count=row.retry_count,
                         created_at=row.created_at, updated_at=row.updated_at)


def save_run(run: IngestionRun) -> None:
    with get_session() as session:
        session.merge(IngestionRunRow(id=run.id, name=run.name, created_at=run.created_at,
                                       completed_at=run.completed_at))
        for job in run.jobs:
            session.merge(_job_to_row(job))
        session.commit()


def get_run(run_id: str) -> IngestionRun | None:
    with get_session() as session:
        run_row = session.get(IngestionRunRow, run_id)
        if run_row is None:
            return None
        job_rows = list(session.exec(select(IngestionJobRow).where(IngestionJobRow.run_id == run_id)))
    return IngestionRun(id=run_row.id, name=run_row.name, jobs=[_row_to_job(r) for r in job_rows],
                         created_at=run_row.created_at, completed_at=run_row.completed_at)


def update_job(job: IngestionJob) -> None:
    with get_session() as session:
        session.merge(_job_to_row(job))
        session.commit()
