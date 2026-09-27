from __future__ import annotations
from shared.domain.types import RetrievalResult


def recall_at_k(results, relevant_ids, k):
    if not relevant_ids:
        return 0.0
    top_k_ids = {r.chunk_id for r in results[:k]}
    hit = len(top_k_ids & relevant_ids)
    return hit / len(relevant_ids)


def precision_at_k(results, relevant_ids, k):
    top_k = results[:k]
    if not top_k:
        return 0.0
    hit = sum(1 for r in top_k if r.chunk_id in relevant_ids)
    return hit / len(top_k)


def mean_reciprocal_rank(results, relevant_ids):
    for i, r in enumerate(results, start=1):
        if r.chunk_id in relevant_ids:
            return 1.0 / i
    return 0.0


def evaluate_run(per_query_results, per_query_relevant_ids, k=5):
    recalls, precisions, rrs = [], [], []
    for query, results in per_query_results.items():
        relevant = per_query_relevant_ids.get(query, set())
        recalls.append(recall_at_k(results, relevant, k))
        precisions.append(precision_at_k(results, relevant, k))
        rrs.append(mean_reciprocal_rank(results, relevant))
    n = max(len(recalls), 1)
    return {f"recall@{k}": sum(recalls) / n, f"precision@{k}": sum(precisions) / n, "mrr": sum(rrs) / n}
