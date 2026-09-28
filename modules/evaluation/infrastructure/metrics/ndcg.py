from __future__ import annotations

import math
from collections.abc import Sequence


def ndcg_at_k(hits: Sequence[frozenset[int]], n_relevant: int, k: int) -> float:
    """Binary-relevance nDCG. A chunk is relevant if it contains any snippet.
    The number of relevant chunks is unknown (relevance is defined by snippets, not
    chunks), so the ideal ranking assumes max(n_snippets, relevant chunks found in
    top-k) relevant chunks, capped at k. This keeps the score within [0, 1]."""
    if n_relevant <= 0:
        return 0.0
    top = hits[:k]
    found = sum(1 for h in top if h)
    dcg = sum(1.0 / math.log2(i + 2) for i, h in enumerate(top) if h)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(max(n_relevant, found), k)))
    return dcg / ideal if ideal else 0.0