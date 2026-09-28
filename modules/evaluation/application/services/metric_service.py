from __future__ import annotations

import re

from modules.evaluation.domain.entities.evaluation_dataset import EvaluationQuery
from modules.evaluation.domain.models.evaluation_result import EvaluationResult
from modules.evaluation.domain.models.metric_result import MetricResult
from modules.evaluation.domain.value_objects.metric_name import MetricName
from modules.evaluation.infrastructure.metrics.mrr import reciprocal_rank
from modules.evaluation.infrastructure.metrics.ndcg import ndcg_at_k
from modules.evaluation.infrastructure.metrics.precision import precision_at_k
from modules.evaluation.infrastructure.metrics.recall import recall_at_k

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return _WS_RE.sub(" ", text).strip().casefold()


def match_snippets(chunk_text: str, snippets: list[str]) -> frozenset[int]:
    """Indices of snippets contained in the chunk (case/whitespace-insensitive)."""
    haystack = normalize(chunk_text)
    out = set()
    for i, s in enumerate(snippets):
        needle = normalize(s)
        if needle and needle in haystack:
            out.add(i)
    return frozenset(out)


class MetricService:
    def evaluate(self, queries: list[EvaluationQuery], ranked_texts: dict[str, list[str]],
                 k: int) -> EvaluationResult:
        """ranked_texts: query -> chunk texts in rank order. Queries missing from it are skipped."""
        per: dict[MetricName, dict[str, float]] = {m: {} for m in MetricName}
        for q in queries:
            texts = ranked_texts.get(q.query)
            if texts is None:
                continue
            hits = [match_snippets(t, q.relevant_texts) for t in texts]
            n = len(q.relevant_texts)
            per[MetricName.RECALL][q.query] = recall_at_k(hits, n, k)
            per[MetricName.PRECISION][q.query] = precision_at_k(hits, k)
            per[MetricName.MRR][q.query] = reciprocal_rank(hits)
            per[MetricName.NDCG][q.query] = ndcg_at_k(hits, n, k)
        metrics = []
        for m in MetricName:
            values = per[m]
            mean = sum(values.values()) / len(values) if values else 0.0
            metrics.append(MetricResult(name=m.label(k), value=mean, per_query=values))
        return EvaluationResult(k=k, num_queries=len(per[MetricName.MRR]), metrics=metrics)
