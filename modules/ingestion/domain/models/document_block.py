from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from modules.ingestion.domain.models.figure import Figure
from modules.ingestion.domain.models.table import Table


class BlockType(str, Enum):
    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    FIGURE = "figure"
    LIST = "list"


@dataclass
class DocumentBlock:
    """A single content unit on a page, in reading order. Carries a Table or
    Figure payload when block_type is TABLE/FIGURE respectively."""

    block_type: BlockType = BlockType.TEXT
    text: str = ""
    position: int = 0
    page_number: int = 0
    heading_level: int = 0  # 1-6 when block_type == HEADING, else 0
    bbox: tuple[float, float, float, float] | None = None
    table: Table | None = None
    figure: Figure | None = None

    def is_structured(self) -> bool:
        return self.block_type in (BlockType.TABLE, BlockType.FIGURE)
