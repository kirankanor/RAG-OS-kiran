from __future__ import annotations

from shared.domain.types import RetrievalResult

_SUMMARY_QUERY = ("Write a 3-5 sentence executive summary of this report for a technical reader. "
                  "Use only facts present in it; do not invent numbers.")


class ArtifactLlmGenerator:
    """Asks a registered Generator (e.g. 'groq_chat') for a short summary of a report. The report
    text is the only context. Any failure returns '' so the report is still produced."""

    def __init__(self, generator, query: str = _SUMMARY_QUERY):
        self.generator = generator
        self.query = query

    def summarize(self, text: str) -> str:
        try:
            answer = self.generator.generate(
                self.query, [RetrievalResult(chunk_id="report", score=1.0, rank=0, text=text)])
        except Exception:  # noqa: BLE001 - the summary is optional
            return ""
        return (answer or "").strip()
