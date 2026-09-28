from __future__ import annotations

from typing import Protocol

from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.entities.strategy_candidate import StrategyCandidate
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig


class CandidateGenerator(Protocol):
    def generate(self, count: int) -> list[StrategyCandidate]: ...


class PresetCandidateGenerator:
    """Fixed baseline candidates. Swap for LlmStrategyGenerator once an LLM is wired in."""

    def generate(self, count: int = 3) -> list[StrategyCandidate]:
        presets = [
            StrategyCandidate(Strategy(
                name="fast-local", description="Cheap, no API keys.",
                chunker=ChunkerConfig("recursive_char", {"chunk_size": 1000, "overlap": 150}),
                embedder=EmbeddingConfig("local_minilm"),
                retrieval=RetrievalConfig("faiss_flat_l2")),
                rationale="Lowest cost and latency; good baseline.", confidence=0.5),
            StrategyCandidate(Strategy(
                name="balanced-hybrid", description="Hybrid retrieval + local reranker.",
                chunker=ChunkerConfig("sentence_window", {"sentences_per_chunk": 5, "sentence_overlap": 1}),
                embedder=EmbeddingConfig("local_minilm"),
                retrieval=RetrievalConfig("hybrid_bm25_vector", {"alpha": 0.5, "fusion_method": "rrf"}),
                reranker=RerankerConfig("cross_encoder")),
                rationale="Lexical + dense recall, reranked for precision.", confidence=0.6),
            StrategyCandidate(Strategy(
                name="quality-cloud", description="Hosted embeddings, Qdrant, Cohere rerank.",
                chunker=ChunkerConfig("recursive_char", {"chunk_size": 800, "overlap": 120}),
                embedder=EmbeddingConfig("openai_text_embedding_3_small"),
                retrieval=RetrievalConfig("qdrant"),
                reranker=RerankerConfig("cohere_rerank")),
                rationale="Highest expected quality; needs API keys and Qdrant.", confidence=0.6),
        ]
        return presets[:max(0, count)]