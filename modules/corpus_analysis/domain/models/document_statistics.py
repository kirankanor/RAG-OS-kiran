from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any


@dataclass(frozen=True)
class DocumentStatistics:
    """Size numbers for the whole corpus. total_pages only counts documents whose
    parser reported num_pages (PDFs)."""

    num_documents: int = 0
    empty_documents: int = 0
    total_chars: int = 0
    total_words: int = 0
    total_pages: int = 0
    min_chars: int = 0
    max_chars: int = 0
    mean_chars: float = 0.0
    median_chars: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DocumentStatistics:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})
