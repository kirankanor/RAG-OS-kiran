#!/usr/bin/env python3
"""Benchmark one or more saved strategies against the same file(s)/queries: wall-clock
time for the full ingest+retrieve pipeline, chunk count, and result count per query.

Usage:
    uv run python scripts/benchmark_pipeline.py <strategy_id> [<strategy_id> ...] \
        --files a.txt b.pdf --queries "how does x work" "what is y"
"""
from __future__ import annotations

import argparse
import sys
import time

from modules.experiments.domain.models.experiment_config import ExperimentConfig
from modules.experiments.infrastructure.runners.retrieval_runner import (
    resolve_top_k, retrieve_for_queries,
)
from modules.experiments.infrastructure.runners.ingestion_runner import build_pipeline
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.exceptions import StrategyNotFoundError


def benchmark_one(strategy_id: str, config: ExperimentConfig) -> dict:
    strategy = StrategyService().get(strategy_id)
    start = time.perf_counter()
    run_config, documents, chunks, retriever, reranker = build_pipeline(config, strategy)
    ingest_seconds = time.perf_counter() - start

    top_k = resolve_top_k(config, strategy)
    start = time.perf_counter()
    by_query = retrieve_for_queries(run_config, retriever, reranker, config.queries, top_k) if config.queries else {}
    retrieve_seconds = time.perf_counter() - start

    return {"strategy": f"{strategy.name} v{strategy.version.number}", "num_documents": len(documents),
            "num_chunks": len(chunks), "ingest_seconds": ingest_seconds, "retrieve_seconds": retrieve_seconds,
            "results_per_query": {q: len(rs) for q, rs in by_query.items()}}


def print_report(rows: list[dict]) -> None:
    header = f"{'strategy':<30}{'docs':>6}{'chunks':>8}{'ingest_s':>10}{'retrieve_s':>12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['strategy']:<30}{r['num_documents']:>6}{r['num_chunks']:>8}"
              f"{r['ingest_seconds']:>10.3f}{r['retrieve_seconds']:>12.3f}")
        for q, n in r["results_per_query"].items():
            print(f"    - {n} result(s) for {q!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("strategy_ids", nargs="+")
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--queries", nargs="*", default=[])
    args = ap.parse_args()

    config = ExperimentConfig(runner="retrieval", file_paths=args.files, queries=args.queries)
    rows = []
    for sid in args.strategy_ids:
        try:
            rows.append(benchmark_one(sid, config))
        except StrategyNotFoundError as e:
            print(f"Skipping {sid}: {e}", file=sys.stderr)
    print_report(rows)


if __name__ == "__main__":
    main()
