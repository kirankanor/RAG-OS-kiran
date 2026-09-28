from __future__ import annotations

from collections.abc import Sequence

from modules.decisions.domain.entities.recommendation import Recommendation
from modules.decisions.domain.models.decision_factor import FACTORS
from modules.decisions.domain.models.tradeoff import Tradeoff

_LABELS = {"quality": "retrieval quality", "latency": "speed", "cost": "cost", "corpus_fit": "corpus fit"}


class TradeoffAnalyzer:
    """Finds where the top runners-up beat the winner, so the reader knows what they
    give up by choosing it."""

    def __init__(self, max_runners_up: int = 3, min_gap: float = 0.05):
        self.max_runners_up = max_runners_up
        self.min_gap = min_gap

    def analyze(self, recommendations: Sequence[Recommendation]) -> list[Tradeoff]:
        eligible = [r for r in recommendations if r.eligible]
        if len(eligible) < 2:
            return []
        winner, runners_up = eligible[0], eligible[1:1 + self.max_runners_up]
        out: list[Tradeoff] = []
        for other in runners_up:
            for name in FACTORS:
                w, o = winner.factor(name), other.factor(name)
                if w is None or o is None or o.score - w.score < self.min_gap:
                    continue
                out.append(Tradeoff(
                    strategy_id=other.strategy_id, strategy_name=other.strategy_name, factor=name,
                    candidate_value=o.display, winner_value=w.display,
                    statement=(f"{other.strategy_name} is better on {_LABELS[name]} ({o.display} vs "
                               f"{w.display}) but ranks lower overall "
                               f"({other.total_score:.2f} vs {winner.total_score:.2f}).")))
        return out
