from __future__ import annotations

from pathlib import Path

from modules.corpus_analysis.domain.models.content_profile import OcrStats
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry


@analyzer_registry.register("ocr", "Flags PDFs with almost no extractable text per page (likely scans).")
class OcrAnalyzer(Analyzer):
    """Heuristic only: needs the parser's num_pages metadata, so non-PDFs are never flagged."""

    name = "ocr"
    produces = "ocr"

    def __init__(self, min_chars_per_page: int = 100):
        self.min_chars_per_page = min_chars_per_page

    def analyze(self, documents):
        docs = list(documents)
        if not docs:
            return OcrStats()
        scanned = []
        for d in docs:
            if Path(d.source_filename).suffix.lower() != ".pdf":
                continue
            pages = int(d.metadata.get("num_pages", 0) or 0)
            if pages > 0 and len(d.text.strip()) / pages < self.min_chars_per_page:
                scanned.append(d.source_filename)
        return OcrStats(likely_scanned_docs=len(scanned),
                        scanned_doc_ratio=round(len(scanned) / len(docs), 3),
                        likely_scanned_files=scanned, ocr_recommended=bool(scanned))
