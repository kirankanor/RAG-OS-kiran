from __future__ import annotations

from modules.strategies.domain.entities.strategy import Strategy

# Relative latency units per component, used only when not every run has a measured
# duration. These are rough heuristics, not benchmarks.
_CHUNKER = {"contextual": 4.0, "semantic": 2.0}
_CHUNKER_DEFAULT = 0.5
_EMBEDDER = {"local_minilm": 1.0, "openai_text_embedding_3_small": 1.5, "cohere_embed_v3": 1.5}
_EMBEDDER_DEFAULT = 1.0
_RETRIEVER = {"faiss_flat_l2": 0.2, "hybrid_bm25_vector": 0.5, "qdrant": 1.0}
_RETRIEVER_DEFAULT = 0.5
_RERANKER = {"cross_encoder": 1.5, "cohere_rerank": 1.0}
_RERANKER_DEFAULT = 1.0


def estimate_latency(strategy: Strategy) -> tuple[float, str]:
    parts = [("chunker", strategy.chunker.name, _CHUNKER.get(strategy.chunker.name, _CHUNKER_DEFAULT)),
             ("embedder", strategy.embedder.name, _EMBEDDER.get(strategy.embedder.name, _EMBEDDER_DEFAULT)),
             ("retriever", strategy.retrieval.name,
              _RETRIEVER.get(strategy.retrieval.name, _RETRIEVER_DEFAULT))]
    if strategy.reranker:
        parts.append(("reranker", strategy.reranker.name,
                      _RERANKER.get(strategy.reranker.name, _RERANKER_DEFAULT)))
    total = sum(v for _, _, v in parts)
    return total, "estimated: " + ", ".join(f"{n}={v:g}" for _, n, v in parts)
