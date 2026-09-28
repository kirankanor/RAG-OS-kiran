from __future__ import annotations

from dataclasses import dataclass

from modules.strategies.domain.entities.strategy import Strategy


@dataclass
class StrategyCandidate:
    """A proposed (not yet saved) strategy, with why it was proposed."""

    strategy: Strategy
    rationale: str = ""
    source: str = "preset"  # "preset" | "llm"
    confidence: float = 0.0