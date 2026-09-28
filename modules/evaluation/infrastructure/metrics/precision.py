from __future__ import annotations

from collections.abc import Sequence


def precision_at_k(hits: Sequence[frozenset[int]], k: int) -> float:
    """Fraction of the (up to k) returned chunks that contain any relevant snippet."""
    top = hits[:k]
    if not top:
        return 0.0
    return sum(1 for h in top if h) / len(top)
