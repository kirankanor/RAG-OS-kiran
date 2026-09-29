from __future__ import annotations

import re
from dataclasses import asdict
from pprint import pformat

from modules.strategies.domain.entities.strategy import Strategy

_SKIP = {"id", "created_at"}

_TEMPLATE = r'''"""Reproduces RAG-OS strategy __TITLE__.

Run from the RAG-OS repo root:
    python __FILENAME__ --files path/a.pdf --queries "your question" --top-k 5
"""
import argparse

from modules.experiments.infrastructure.pipeline_orchestration import run_dataset_generation
from modules.experiments.infrastructure.runners.retrieval_runner import retrieve_for_queries
from shared.domain.types import RunConfig

CONFIG = __CONFIG__
DEFAULT_TOP_K = __TOP_K__
__NOTES__

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--queries", nargs="+", default=[])
    ap.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    args = ap.parse_args()

    run_config = RunConfig(**CONFIG)
    _, documents, chunks, retriever, reranker = run_dataset_generation(args.files, run_config)
    print(f"{len(documents)} document(s), {len(chunks)} chunk(s) indexed")
    if not args.queries:
        return
    by_query = retrieve_for_queries(run_config, retriever, reranker, args.queries, args.top_k)
    for query, results in by_query.items():
        print(f"\n## {query}")
        for r in results:
            print(f"[{r.rank + 1}] {r.score:.4f}  {r.text[:200]!r}")


if __name__ == "__main__":
    main()
'''


def slugify(text: str, default: str = "item") -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-._") or default


def script_filename(strategy: Strategy) -> str:
    return f"{slugify(strategy.name, 'strategy')}_v{strategy.version.number}.py"


def generate_strategy_script(strategy: Strategy, filename: str = "") -> str:
    """A standalone script that rebuilds the strategy's pipeline and runs queries through it."""
    config = {k: v for k, v in asdict(strategy.to_run_config()).items() if k not in _SKIP}
    notes = ""
    if strategy.chunker.name == "contextual":
        notes = ("# NOTE: the 'contextual' chunker needs an llm_fn that run_dataset_generation does\n"
                 "# not supply, so this strategy will fail until you wire one in.\n")
    title = f"'{strategy.name}' v{strategy.version.number}".replace('"', "'")
    return (_TEMPLATE.replace("__TITLE__", title)
            .replace("__FILENAME__", filename or script_filename(strategy))
            .replace("__CONFIG__", pformat(config, sort_dicts=False, width=88))
            .replace("__TOP_K__", str(strategy.retrieval.top_k))
            .replace("__NOTES__", notes))
