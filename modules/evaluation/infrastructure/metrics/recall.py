from __future__ import annotations

from collections.abc import Sequence


def recall_at_k(hits: Sequence[frozenset[int]], n_relevant: int, k: int) -> float:
    """hits[i] = indices of relevant snippets contained in the i-th ranked chunk.
    Recall = fraction of relevant snippets covered by the top-k chunks."""
    if n_relevant <= 0:
        return 0.0
    covered: set[int] = set()
    for h in hits[:k]:
        covered |= h
    return len(covered) / n_relevant
