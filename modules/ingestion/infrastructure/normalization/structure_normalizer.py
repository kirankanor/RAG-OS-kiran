from __future__ import annotations

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.interfaces.normalizer import Normalizer, normalizer_registry
from modules.ingestion.domain.models.document_block import BlockType


@normalizer_registry.register(
    "structure_normalizer",
    "Drops empty text blocks, clamps heading levels, and re-sequences block positions.",
)
class StructureNormalizer(Normalizer):
    name = "structure_normalizer"

    def normalize(self, document: CanonicalDocument) -> CanonicalDocument:
        for page in document.pages:
            kept = []
            for block in page.blocks:
                if block.block_type == BlockType.TEXT and not block.text.strip():
                    continue
                if block.block_type == BlockType.HEADING:
                    block.heading_level = max(1, min(6, block.heading_level or 1))
                kept.append(block)
            for position, block in enumerate(kept):
                block.position = position
            page.blocks = kept
        return document
