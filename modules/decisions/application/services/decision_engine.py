from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from modules.decisions.domain.entities.recommendation import Recommendation
from modules.decisions.domain.exceptions import InvalidDecisionError
from modules.decisions.domain.models.constraint import Constraint
from modules.decisions.domain.models.decision_factor import (
    FACTOR_COST, FACTOR_CORPUS_FIT, FACTOR_LATENCY, FACTOR_QUALITY, DecisionFactor,
)
from modules.decisions.domain.rules.cost_rules import estimate_cost
from modules.decisions.domain.rules.latency_rules import estimate_latency
from modules.decisions.domain.rules.quality_rules import corpus_fit, quality_value
from modules.decisions.domain.rules.scoring import lower_is_better, normalize_weights
from modules.strategies.domain.entities.strategy import Strategy

DEFAULT_WEIGHTS: dict[str, float] = {FACTOR_QUALITY: 0.6, FACTOR_LATENCY: 0.15,
                                     FACTOR_COST: 0.15, FACTOR_CORPUS_FIT: 0.10}


@dataclass
class CandidateInput:
    """One strategy plus what is known about how it performed."""

    strategy: Strategy
    quality_metrics: dict[str, float] = field(default_factory=dict)  # EvaluationResult.summary()
    latency_seconds: float | None = None                             # ExperimentRun.duration_seconds


class DecisionEngine:
    """Pure scoring: no database, no other services. Scores each candidate on quality,
    latency, cost and (if corpus features are given) corpus fit, combines them with the
    weights, applies hard constraints and ranks. Eligible candidates rank first."""

    def decide(self, candidates: Sequence[CandidateInput], constraints: Sequence[Constraint] = (),
               corpus_features: Mapping[str, Any] | None = None,
               weights: Mapping[str, float] | None = None) -> tuple[list[Recommendation], dict[str, float]]:
        cands = list(candidates)
        if not cands:
            raise InvalidDecisionError("No candidates to compare.", ["No candidates to compare."])
        has_fit = corpus_features is not None
        used = normalize_weights(weights if weights is not None else DEFAULT_WEIGHTS,
                                 drop=() if has_fit else (FACTOR_CORPUS_FIT,))

        quality = [quality_value(c.quality_metrics) for c in cands]
        cost = [estimate_cost(c.strategy) for c in cands]
        measured = all(c.latency_seconds is not None for c in cands)
        if measured:
            latency = [(float(c.latency_seconds), "measured run time") for c in cands]
            latency_unit = "s"
        else:
            latency = [estimate_latency(c.strategy) for c in cands]
            latency_unit = "units"
        latency_scores = lower_is_better([v for v, _ in latency])
        cost_scores = lower_is_better([v for v, _ in cost])
        fits = [corpus_fit(c.strategy, corpus_features) for c in cands] if has_fit else []

        recs: list[Recommendation] = []
        for i, c in enumerate(cands):
            factors = [
                DecisionFactor(FACTOR_QUALITY, quality[i][0], quality[i][0], used.get(FACTOR_QUALITY, 0.0),
                               "", quality[i][1]),
                DecisionFactor(FACTOR_LATENCY, latency[i][0], latency_scores[i], used.get(FACTOR_LATENCY, 0.0),
                               latency_unit, latency[i][1]),
                DecisionFactor(FACTOR_COST, cost[i][0], cost_scores[i], used.get(FACTOR_COST, 0.0),
                               "units", cost[i][1]),
            ]
            warnings: list[str] = []
            if has_fit:
                fit = fits[i]
                factors.append(DecisionFactor(FACTOR_CORPUS_FIT, fit.score, fit.score,
                                              used.get(FACTOR_CORPUS_FIT, 0.0), "",
                                              "; ".join(fit.notes) or "no corpus-specific match"))
                warnings = list(fit.warnings)
            raw = {"quality": quality[i][0], "latency": latency[i][0], "cost": cost[i][0]}
            violated = [k.describe_violation(raw[k.metric]) for k in constraints
                        if not k.is_satisfied(raw[k.metric])]
            recs.append(Recommendation(
                strategy_id=str(c.strategy.id), strategy_version=c.strategy.version.number,
                strategy_name=c.strategy.name, total_score=round(sum(f.weighted_score for f in factors), 4),
                eligible=not violated, factors=factors, violated_constraints=violated, warnings=warnings))

        recs.sort(key=lambda r: (not r.eligible, -r.total_score, r.factor(FACTOR_COST).value, r.strategy_name))
        for rank, r in enumerate(recs, start=1):
            r.rank = rank
        return recs, used
