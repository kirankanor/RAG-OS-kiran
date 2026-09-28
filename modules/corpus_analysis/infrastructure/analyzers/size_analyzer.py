from __future__ import annotations

import statistics

from modules.corpus_analysis.domain.models.document_statistics import DocumentStatistics
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry


@analyzer_registry.register("size", "Document counts and character/word/page size statistics.")
class SizeAnalyzer(Analyzer):
    name = "size"
    produces = "statistics"

    def analyze(self, documents):
        docs = list(documents)
        if not docs:
            return DocumentStatistics()
        lengths = [len(d.text) for d in docs]
        return DocumentStatistics(
            num_documents=len(docs),
            empty_documents=sum(1 for d in docs if not d.text.strip()),
            total_chars=sum(lengths),
            total_words=sum(len(d.text.split()) for d in docs),
            total_pages=sum(int(d.metadata.get("num_pages", 0) or 0) for d in docs),
            min_chars=min(lengths), max_chars=max(lengths),
            mean_chars=round(statistics.fmean(lengths), 1),
            median_chars=float(statistics.median(lengths)),
        )
