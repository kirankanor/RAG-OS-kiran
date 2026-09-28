from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any


@dataclass(frozen=True)
class StructureProfile:
    """How much explicit structure the text carries (headings, lists, code)."""

    num_paragraphs: int = 0
    avg_paragraph_chars: float = 0.0
    num_headings: int = 0
    docs_with_headings: int = 0
    heading_doc_ratio: float = 0.0
    num_list_items: int = 0
    num_code_lines: int = 0
    code_line_ratio: float = 0.0

    @property
    def structure_level(self) -> str:
        """'structured' (most docs have headings), 'semi' (some), or 'flat' (none)."""
        if self.num_headings == 0:
            return "flat"
        return "structured" if self.heading_doc_ratio >= 0.6 else "semi"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> StructureProfile:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})
