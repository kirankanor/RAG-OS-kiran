from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyVersion:
    """Version of a saved, named strategy config. Distinct from
    ingestion's ProcessingVersion, which stamps a specific ingestion output."""

    number: int = 1

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Version number must be >= 1.")

    def bumped(self) -> StrategyVersion:
        return StrategyVersion(self.number + 1)

    def __str__(self) -> str:
        return f"v{self.number}"