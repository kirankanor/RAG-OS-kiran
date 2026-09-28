from __future__ import annotations

from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig


class CreateStrategyCommand:
    def __init__(self, service: StrategyService | None = None):
        self.service = service or StrategyService()

    def execute(self, name: str, chunker: ChunkerConfig, embedder: EmbeddingConfig,
                retrieval: RetrievalConfig, parser: ParserConfig | None = None,
                reranker: RerankerConfig | None = None, description: str = "") -> Strategy:
        return self.service.create(name, parser or ParserConfig(), chunker, embedder, retrieval,
                                   reranker, description)