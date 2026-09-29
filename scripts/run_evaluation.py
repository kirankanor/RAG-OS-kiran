#!/usr/bin/env python3
"""Run (or re-run) an evaluation of a finished experiment against a dataset, and print
a comparison table.

Usage:
    uv run python scripts/run_evaluation.py <dataset_id> <experiment_id> [--k 5] [--sort-by mrr]
"""
from __future__ import annotations

import argparse
import sys

from modules.evaluation.application.commands.compare_results import CompareResultsCommand
from modules.evaluation.application.commands.run_evaluation import RunEvaluationCommand
from modules.evaluation.domain.exceptions import EvaluationError
from modules.experiments.application.queries.get_experiment import GetExperimentQuery
from modules.experiments.domain.exceptions import ExperimentNotFoundError


def _print_table(rows: list[tuple[str, str]]) -> None:
    if not rows:
        print("  (no rows)")
        return
    width = max(len(a) for a, _ in rows)
    for a, b in rows:
        print(f"  {a.ljust(width)}  {b}")


def run(dataset_id: str, experiment_id: str, k: int | None, sort_by: str) -> None:
    try:
        experiment = GetExperimentQuery().execute(experiment_id)
    except ExperimentNotFoundError as e:
        sys.exit(f"Error: {e}")
    if not experiment.status.is_terminal:
        sys.exit(f"Error: experiment '{experiment_id}' is {experiment.status.value}; wait for it to finish.")

    try:
        eval_runs = RunEvaluationCommand().execute(dataset_id, experiment_id, k)
    except EvaluationError as e:
        sys.exit(f"Error: {e}")
    print(f"Evaluated {len(eval_runs)} run(s) for experiment '{experiment.name}':")
    _print_table([(r.strategy_id, r.status.value if r.status.value == "completed"
                   else f"FAILED: {r.error_message}") for r in eval_runs])

    ranked = CompareResultsCommand().execute(dataset_id, experiment_id, sort_by)
    print(f"\nRanked by '{sort_by}' (best first):")
    _print_table([(r.strategy_id, ", ".join(f"{k}={v:.3f}" for k, v in r.result.summary().items())
                   if r.status.value == "completed" else "FAILED")
                  for r in ranked])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("dataset_id")
    ap.add_argument("experiment_id")
    ap.add_argument("--k", type=int, default=None, help="Override top-k (default: each run's own top_k).")
    ap.add_argument("--sort-by", default="mrr", help="Metric kind to rank by (recall, precision, mrr, ndcg).")
    args = ap.parse_args()
    run(args.dataset_id, args.experiment_id, args.k, args.sort_by)


if __name__ == "__main__":
    main()
