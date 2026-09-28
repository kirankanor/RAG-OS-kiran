from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from modules.decisions.domain.exceptions import InvalidDecisionError
from modules.decisions.domain.models.decision_factor import FACTORS


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def lower_is_better(values: Sequence[float]) -> list[float]:
    """Min-max normalize so the smallest value scores 1.0 and the largest 0.0.
    If all values are equal nobody is penalized (all 1.0)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [1.0] * len(values)
    return [(hi - v) / (hi - lo) for v in values]


def normalize_weights(weights: Mapping[str, float], drop: Iterable[str] = ()) -> dict[str, float]:
    """Validate and scale weights to sum to 1. The mapping is taken as complete: a factor
    that is missing gets weight 0. Factors in `drop` are removed before scaling."""
    errors = [f"Unknown weight '{k}'. Available: {list(FACTORS)}" for k in weights if k not in FACTORS]
    errors += [f"Weight '{k}' must be >= 0." for k, v in weights.items() if v < 0]
    if errors:
        raise InvalidDecisionError("Invalid weights: " + "; ".join(errors), errors)
    kept = {k: float(v) for k, v in weights.items() if k not in set(drop)}
    total = sum(kept.values())
    if total <= 0:
        raise InvalidDecisionError("Invalid weights: at least one applicable weight must be > 0.",
                                   ["No positive weight."])
    return {k: v / total for k, v in kept.items()}
