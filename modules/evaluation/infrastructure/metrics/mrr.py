from __future__ import annotations

from collections.abc import Sequence


def reciprocal_rank(hits: Sequence[frozenset[int]]) -> float:
    for i, h in enumerate(hits, start=1):
        if h:
            return 1.0 / i
    return 0.0
