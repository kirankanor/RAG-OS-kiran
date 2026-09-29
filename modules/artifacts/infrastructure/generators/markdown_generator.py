from __future__ import annotations

from modules.decisions.domain.entities.decision import Decision
from modules.decisions.domain.models.decision_factor import FACTORS

_LABELS = {"quality": "Quality", "latency": "Latency", "cost": "Cost", "corpus_fit": "Corpus fit"}


def _cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_decision_report(decision: Decision, summary: str = "") -> str:
    """Markdown report for a Decision. `summary` (optional, e.g. LLM-written) goes on top."""
    recs = decision.recommendations
    lines = ["# Strategy recommendation", "",
             f"- Experiment: `{decision.experiment_id}`", f"- Dataset: `{decision.dataset_id}`"]
    if decision.corpus_profile_id:
        lines.append(f"- Corpus profile: `{decision.corpus_profile_id}`")
    lines += [f"- Decision: `{decision.id}` ({decision.created_at})", ""]
    if summary.strip():
        lines += ["## Summary", "", summary.strip(), ""]

    lines += ["## Recommendation", ""]
    w = decision.winner
    if w:
        lines.append(f"**{w.strategy_name}** v{w.strategy_version} "
                     f"(score {w.total_score:.2f}, best of {sum(r.eligible for r in recs)} eligible).")
    else:
        lines.append("No strategy satisfied all constraints.")
    lines.append("")

    if recs:
        names = [n for n in FACTORS if any(r.factor(n) is not None for r in recs)]
        lines += ["## Ranking", "",
                  "| " + " | ".join(["Rank", "Strategy", "Score", "Eligible"] + [_LABELS[n] for n in names]) + " |",
                  "|" + "---|" * (4 + len(names))]
        for r in recs:
            cells = [r.rank, f"{r.strategy_name} v{r.strategy_version}", f"{r.total_score:.2f}",
                     "yes" if r.eligible else "no"]
            cells += [f.display if (f := r.factor(n)) is not None else "-" for n in names]
            lines.append("| " + " | ".join(_cell(c) for c in cells) + " |")
        lines.append("")
        excluded = [r for r in recs if not r.eligible]
        if excluded:
            lines += ["## Excluded", ""]
            lines += [f"- {r.strategy_name} v{r.strategy_version}: " + "; ".join(r.violated_constraints)
                      for r in excluded]
            lines.append("")

    if decision.weights:
        lines += ["## Weights", ""] + [f"- {k}: {v:.2f}" for k, v in sorted(decision.weights.items())] + [""]
    if decision.constraints:
        lines += ["## Constraints", ""] + [f"- {c.metric} {c.operator} {c.value:g}"
                                            for c in decision.constraints] + [""]
    if decision.tradeoffs:
        lines += ["## Trade-offs", ""] + [f"- {t.statement}" for t in decision.tradeoffs] + [""]
    warnings = list(decision.warnings) + [f"{r.strategy_name}: {m}" for r in recs for m in r.warnings]
    if warnings:
        lines += ["## Warnings", ""] + [f"- {m}" for m in warnings] + [""]
    if decision.explanation.strip():
        lines += ["## Explanation", "", decision.explanation.strip(), ""]
    return "\n".join(lines).rstrip() + "\n"
