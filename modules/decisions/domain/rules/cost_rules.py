from __future__ import annotations

from modules.strategies.domain.entities.strategy import Strategy

# Relative cost units per component (0 = free/local). Heuristic: hosted APIs and
# services you must run cost more than local models. Unknown components count as 0.
_CHUNKER = {"contextual": 3.0, "semantic": 1.0}   # LLM call per chunk / extra embedding calls
_EMBEDDER = {"openai_text_embedding_3_small": 1.0, "cohere_embed_v3": 1.0}
_RETRIEVER = {"qdrant": 0.5}                       # needs a running vector DB
_RERANKER = {"cohere_rerank": 1.0, "cross_encoder": 0.25}


def estimate_cost(strategy: Strategy) -> tuple[float, str]:
    parts = [(strategy.chunker.name, _CHUNKER.get(strategy.chunker.name, 0.0)),
             (strategy.embedder.name, _EMBEDDER.get(strategy.embedder.name, 0.0)),
             (strategy.retrieval.name, _RETRIEVER.get(strategy.retrieval.name, 0.0))]
    if strategy.reranker:
        parts.append((strategy.reranker.name, _RERANKER.get(strategy.reranker.name, 0.0)))
    total = sum(v for _, v in parts)
    paid = [f"{n}={v:g}" for n, v in parts if v]
    return total, "relative units: " + (", ".join(paid) if paid else "all local")
