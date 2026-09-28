from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

# Side-effect imports: register validators / normalizers / OCR engines / parsers / chunkers.
from modules.ingestion.infrastructure import normalization, ocr, validation  # noqa: F401
from modules.ingestion.infrastructure.chunkers import chunker_registry
from modules.ingestion.infrastructure.normalization import normalizer_registry
from modules.ingestion.infrastructure.ocr import ocr_registry
from modules.ingestion.infrastructure.parsers import parser_for_file, parser_registry
from modules.ingestion.infrastructure.validation import validator_registry
from modules.ingestion.infrastructure.persistence import repository  # noqa: F401  (registers "sql" storage)

from modules.ingestion.application.dto.ingestion_dto import StartIngestionDTO
from modules.ingestion.application.services.stage_runner import StageRunner
from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.entities.ingestion_job import IngestionJob
from modules.ingestion.domain.exceptions import ValidationFailedError
from modules.ingestion.domain.interfaces.storage import DocumentStorage, document_storage_registry
from modules.ingestion.domain.models.document_block import BlockType, DocumentBlock
from modules.ingestion.domain.models.page import Page
from modules.ingestion.domain.value_objects.processing_stage import ProcessingStage
from modules.ingestion.domain.value_objects.processing_version import ProcessingVersion
from shared.domain.types import Chunk, Document

# Validators run against different targets, so route them by name.
_FILE_VALIDATORS = {"file_validator"}         # target: file path
_DOCUMENT_VALIDATORS = {"extraction_validator"}  # target: CanonicalDocument
_CHUNK_VALIDATORS = {"quality_validator"}     # target: list[Chunk]


@dataclass
class PipelineResult:
    canonical: CanonicalDocument
    chunks: list[Chunk]
    warnings: list[str] = field(default_factory=list)


def _params_hash(params: dict[str, Any]) -> str:
    raw = json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _to_canonical(document: Document) -> CanonicalDocument:
    """Bridge from the flat parsed Document to the page/block form. Existing
    parsers return flat text only, so this is one page of paragraph blocks."""
    paragraphs = [p for p in re.split(r"\n\s*\n", document.text) if p.strip()]
    blocks = [DocumentBlock(block_type=BlockType.TEXT, text=p, position=i, page_number=1)
              for i, p in enumerate(paragraphs)]
    return CanonicalDocument(source_document_id=document.id, source_filename=document.source_filename,
                             pages=[Page(page_number=1, blocks=blocks)], stage=ProcessingStage.PARSING)


def _to_document(canonical: CanonicalDocument, original: Document) -> Document:
    """Back to a flat Document for the existing chunkers. Blocks are joined
    with blank lines so paragraph-aware chunkers still see boundaries."""
    text = "\n\n".join(b.text for p in canonical.pages for b in p.blocks if b.text.strip())
    return Document(id=original.id, source_filename=original.source_filename, text=text,
                    parser_name=original.parser_name, metadata=dict(original.metadata))


class PipelineRunner:
    """Runs one file through: validate -> parse -> (ocr) -> normalize+validate+persist -> chunk.
    Embedding/indexing are experiment-level concerns and are not done here."""

    def __init__(self, config: StartIngestionDTO, stage_runner: StageRunner | None = None,
                 storage: DocumentStorage | None = None):
        self.config = config
        self.stage_runner = stage_runner or StageRunner()
        self.storage = storage or document_storage_registry.create("sql")
        self._file_validators, self._document_validators, self._chunk_validators = [], [], []
        for name in config.validators:
            if name in _FILE_VALIDATORS:
                self._file_validators.append(validator_registry.create(name))
            elif name in _DOCUMENT_VALIDATORS:
                self._document_validators.append(validator_registry.create(name))
            elif name in _CHUNK_VALIDATORS:
                self._chunk_validators.append(validator_registry.create(name))
            else:
                raise ValueError(f"Unknown validator '{name}'.")
        self._normalizers = [normalizer_registry.create(n) for n in config.normalizers]
        self._ocr = ocr_registry.create(config.ocr_engine) if config.ocr_engine else None
        self._chunker = chunker_registry.create(config.chunker_name, **config.chunker_params)

    def process(self, job: IngestionJob, file_path: str) -> PipelineResult:
        run_stage = self.stage_runner.run
        warnings: list[str] = []
        run_stage(job, ProcessingStage.VALIDATING, self._check, self._file_validators, file_path, warnings)
        document = run_stage(job, ProcessingStage.PARSING, self._parse, file_path)
        canonical = _to_canonical(document)
        canonical.version = ProcessingVersion(
            parser_name=document.parser_name, parser_params_hash=_params_hash(self.config.parser_params),
            chunker_name=self.config.chunker_name, chunker_params_hash=_params_hash(self.config.chunker_params))
        if self._ocr is not None:
            run_stage(job, ProcessingStage.OCR, self._ocr_figures, canonical)
        run_stage(job, ProcessingStage.NORMALIZING, self._normalize, canonical, warnings)
        chunks = run_stage(job, ProcessingStage.CHUNKING, self._chunk, canonical, document, warnings)
        return PipelineResult(canonical=canonical, chunks=chunks, warnings=warnings)

    # --- stage bodies -------------------------------------------------------

    @staticmethod
    def _check(validators, target, warnings: list[str]) -> None:
        for v in validators:
            result = v.validate(target)
            warnings.extend(f"[{v.name}] {w}" for w in result.warnings)
            if not result.is_valid:
                raise ValidationFailedError(f"{v.name} rejected input: " + "; ".join(result.errors),
                                            errors=result.errors)

    def _parse(self, file_path: str) -> Document:
        if self.config.parser_name == "auto_by_extension":
            parser = parser_for_file(file_path)
        else:
            parser = parser_registry.create(self.config.parser_name, **self.config.parser_params)
        return parser.parse(file_path)

    def _ocr_figures(self, canonical: CanonicalDocument) -> None:
        for page in canonical.pages:
            for block in page.blocks:
                fig = block.figure
                if fig and fig.image_path and not fig.ocr_text:
                    fig.ocr_text = self._ocr.extract_text(fig.image_path)
                    if fig.ocr_text.strip() and not block.text:
                        block.text = fig.ocr_text

    def _normalize(self, canonical: CanonicalDocument, warnings: list[str]) -> None:
        for normalizer in self._normalizers:
            normalizer.normalize(canonical)
        self._check(self._document_validators, canonical, warnings)
        canonical.stage = ProcessingStage.NORMALIZING
        self.storage.save(canonical)

    def _chunk(self, canonical: CanonicalDocument, original: Document, warnings: list[str]) -> list[Chunk]:
        chunks = self._chunker.chunk(_to_document(canonical, original))
        self._check(self._chunk_validators, chunks, warnings)
        return chunks
