from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValueObject:
    """Marker base for immutable value objects (StrategyId, DocumentHash, ...). Existing
    value objects already follow this shape (@dataclass(frozen=True, slots=True)) by
    convention; inheriting from this is optional, not required for the pattern to work."""
