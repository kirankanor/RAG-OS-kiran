from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


def _pick(cls, d: dict[str, Any]):
    names = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in (d or {}).items() if k in names})


@dataclass(frozen=True)
class TableStats:
    num_tables: int = 0
    docs_with_tables: int = 0
    table_doc_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TableStats:
        return _pick(cls, d)


@dataclass(frozen=True)
class DuplicateStats:
    exact_duplicate_docs: int = 0      # extra copies beyond the first of identical docs
    near_duplicate_pairs: int = 0      # distinct docs with very high shingle overlap
    duplicate_doc_ratio: float = 0.0
    duplicate_paragraph_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DuplicateStats:
        return _pick(cls, d)


@dataclass(frozen=True)
class OcrStats:
    likely_scanned_docs: int = 0
    scanned_doc_ratio: float = 0.0
    likely_scanned_files: list[str] = field(default_factory=list)
    ocr_recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> OcrStats:
        return _pick(cls, d)


@dataclass(frozen=True)
class ContentProfile:
    """What kinds of content the corpus contains beyond plain prose."""

    tables: TableStats = field(default_factory=TableStats)
    duplicates: DuplicateStats = field(default_factory=DuplicateStats)
    ocr: OcrStats = field(default_factory=OcrStats)

    def to_dict(self) -> dict[str, Any]:
        return {"tables": self.tables.to_dict(), "duplicates": self.duplicates.to_dict(),
                "ocr": self.ocr.to_dict()}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> ContentProfile:
        d = d or {}
        return cls(tables=TableStats.from_dict(d.get("tables", {})),
                   duplicates=DuplicateStats.from_dict(d.get("duplicates", {})),
                   ocr=OcrStats.from_dict(d.get("ocr", {})))
