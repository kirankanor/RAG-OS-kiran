from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Table:
    """A structured table extracted from a page."""

    rows: list[list[str]] = field(default_factory=list)
    caption: str = ""
    page_number: int = 0
    bbox: tuple[float, float, float, float] | None = None  # (x0, y0, x1, y1)

    @property
    def num_rows(self) -> int:
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    def to_text(self) -> str:
        return "\n".join(" | ".join(cell.strip() for cell in row) for row in self.rows)
