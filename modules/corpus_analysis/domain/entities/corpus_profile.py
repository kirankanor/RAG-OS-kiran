from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from modules.corpus_analysis.domain.models.content_profile import ContentProfile
from modules.corpus_analysis.domain.models.document_statistics import DocumentStatistics
from modules.corpus_analysis.domain.models.language_profile import LanguageProfile
from modules.corpus_analysis.domain.models.structure_profile import StructureProfile


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class CorpusProfile:
    """The measured characteristics of a document set. Sections whose analyzer was
    not run keep their empty defaults."""

    id: str = field(default_factory=_new_id)
    analysis_run_id: str = ""
    statistics: DocumentStatistics = field(default_factory=DocumentStatistics)
    structure: StructureProfile = field(default_factory=StructureProfile)
    language: LanguageProfile = field(default_factory=LanguageProfile)
    content: ContentProfile = field(default_factory=ContentProfile)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_utcnow)

    def features(self) -> dict[str, Any]:
        """Flat, scalar summary. Intended input for the decisions module's rules."""
        s, st, lg, c = self.statistics, self.structure, self.language, self.content
        return {
            "num_documents": s.num_documents, "total_chars": s.total_chars,
            "mean_doc_chars": s.mean_chars, "median_doc_chars": s.median_chars,
            "avg_paragraph_chars": st.avg_paragraph_chars, "structure_level": st.structure_level,
            "heading_doc_ratio": st.heading_doc_ratio, "code_line_ratio": st.code_line_ratio,
            "primary_language": lg.primary_language, "is_multilingual": lg.is_multilingual,
            "table_doc_ratio": c.tables.table_doc_ratio,
            "duplicate_doc_ratio": c.duplicates.duplicate_doc_ratio,
            "scanned_doc_ratio": c.ocr.scanned_doc_ratio, "ocr_recommended": c.ocr.ocr_recommended,
        }

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "analysis_run_id": self.analysis_run_id,
                "statistics": self.statistics.to_dict(), "structure": self.structure.to_dict(),
                "language": self.language.to_dict(), "content": self.content.to_dict(),
                "warnings": list(self.warnings), "created_at": self.created_at}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CorpusProfile:
        return cls(id=d.get("id", _new_id()), analysis_run_id=d.get("analysis_run_id", ""),
                   statistics=DocumentStatistics.from_dict(d.get("statistics", {})),
                   structure=StructureProfile.from_dict(d.get("structure", {})),
                   language=LanguageProfile.from_dict(d.get("language", {})),
                   content=ContentProfile.from_dict(d.get("content", {})),
                   warnings=list(d.get("warnings", [])), created_at=d.get("created_at", _utcnow()))
