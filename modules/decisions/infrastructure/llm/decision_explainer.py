from __future__ import annotations

from typing import Protocol

from modules.decisions.domain.entities.decision import Decision
from modules.decisions.domain.models.decision_factor import FACTORS
from shared.domain.types import RetrievalResult

_LABELS = {"quality": "quality", "latency": "latency", "cost": "cost", "corpus_fit": "corpus fit"}
_LLM_QUERY = ("Explain in 3-5 sentences why the recommended strategy was chosen and what "
              "trade-offs the reader should know about. Do not invent numbers.")


class DecisionExplainer(Protocol):
    def explain(self, decision: Decision) -> str: ...


class TemplateExplainer:
    """Deterministic explanation built straight from the decision. Needs no LLM."""

    def explain(self, decision: Decision) -> str:
        recs = decision.recommendations
        lines: list[str] = []
        winner = decision.winner
        if winner is not None:
            eligible = sum(1 for r in recs if r.eligible)
            lines.append(f"Recommended: {winner.strategy_name} v{winner.strategy_version} "
                         f"(score {winner.total_score:.2f}, best of {eligible} eligible).")
            parts = [f"{_LABELS[n]} {f.display}" for n in FACTORS if (f := winner.factor(n)) is not None]
            lines.append("Its numbers: " + ", ".join(parts) + ".")
            lines.extend(t.statement for t in decision.tradeoffs)
        else:
            lines.append("No strategy satisfied all constraints.")
            if recs:
                best = recs[0]
                lines.append(f"Closest by score: {best.strategy_name} v{best.strategy_version} "
                             f"({best.total_score:.2f}).")
        for r in recs:
            if not r.eligible:
                lines.append(f"Excluded {r.strategy_name} v{r.strategy_version}: "
                             + "; ".join(r.violated_constraints) + ".")
        lines.extend(f"Warning: {w}" for w in decision.warnings)
        if winner is not None:
            lines.extend(f"Warning ({winner.strategy_name}): {w}" for w in winner.warnings)
        return "\n".join(lines)


class LlmExplainer:
    """Asks a registered Generator (e.g. 'groq_chat') to phrase the explanation. The
    template text is passed as the only context, so the model restates facts instead of
    inventing them. Any failure falls back to the template explanation."""

    def __init__(self, generator, fallback: DecisionExplainer | None = None):
        self.generator = generator
        self.fallback = fallback or TemplateExplainer()

    def explain(self, decision: Decision) -> str:
        facts = self.fallback.explain(decision)
        try:
            answer = self.generator.generate(
                _LLM_QUERY, [RetrievalResult(chunk_id="decision", score=1.0, rank=0, text=facts)])
        except Exception:  # noqa: BLE001 - explanation is optional, the decision must still be saved
            return facts
        return answer.strip() or facts
