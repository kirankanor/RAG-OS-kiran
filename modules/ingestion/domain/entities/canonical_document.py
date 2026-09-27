from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.ingestion.domain.models.page import Page
from modules.ingestion.domain.value_objects.processing_stage import ProcessingStage
from modules.ingestion.domain.value_objects.processing_version import ProcessingVersion


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class CanonicalDocument:
    """The structured, normalized output of parsing+normalization for one
    source file: a page-by-page breakdown ready for chunking.

    Distinct from shared.domain.types.Document, which is the flat raw-text +
    metadata form already consumed by the working chunkers. CanonicalDocument
    is the richer intermediate representation OCR/normalization stages will
    produce once implemented; source_document_id ties it back to the
    corresponding shared.domain.types.Document.
    """

    id: str = field(default_factory=_new_id)
    source_document_id: str = ""
    source_filename: str = ""
    pages: list[Page] = field(default_factory=list)
    stage: ProcessingStage = ProcessingStage.UPLOADED
    version: ProcessingVersion | None = None
    created_at: str = field(default_factory=_utcnow)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @property
    def num_pages(self) -> int:
        return len(self.pages)
