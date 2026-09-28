from __future__ import annotations

import re

from modules.corpus_analysis.domain.models.content_profile import TableStats
from modules.corpus_analysis.infrastructure.analyzers.base import Analyzer, analyzer_registry

_GAP_RE = re.compile(r"\s{2,}")


def _is_table_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if " | " in s or (s.startswith("|") and s.endswith("|")):  # markdown, or docx rows joined with ' | '
        return True
    if s.count("\t") >= 2:
        return True
    cells = [c for c in _GAP_RE.split(s) if c]  # whitespace-aligned columns
    return len(cells) >= 3 and all(len(c) <= 30 for c in cells)


@analyzer_registry.register("tables", "Table-like blocks: pipe/markdown rows, tab-separated or aligned columns.")
class TableAnalyzer(Analyzer):
    """A table is a run of at least two consecutive table-like lines."""

    name = "tables"
    produces = "tables"

    def analyze(self, documents):
        docs = list(documents)
        if not docs:
            return TableStats()
        total = docs_with = 0
        for d in docs:
            run, found = 0, 0
            for line in d.text.splitlines():
                if _is_table_line(line):
                    run += 1
                    continue
                found += 1 if run >= 2 else 0
                run = 0
            found += 1 if run >= 2 else 0
            total += found
            docs_with += 1 if found else 0
        return TableStats(num_tables=total, docs_with_tables=docs_with,
                          table_doc_ratio=round(docs_with / len(docs), 3))
