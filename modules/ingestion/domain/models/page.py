from __future__ import annotations

from dataclasses import dataclass, field

from modules.ingestion.domain.models.document_block import BlockType, DocumentBlock


@dataclass
class Page:
    """A single page of a parsed document, holding its blocks in reading order."""

    page_number: int = 0
    blocks: list[DocumentBlock] = field(default_factory=list)
    width: float = 0.0
    height: float = 0.0

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks if b.text)

    def blocks_of_type(self, block_type: BlockType) -> list[DocumentBlock]:
        return [b for b in self.blocks if b.block_type == block_type]
