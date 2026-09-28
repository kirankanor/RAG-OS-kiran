from __future__ import annotations

from sqlmodel import SQLModel

from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.exceptions import InvalidStrategyError, StrategyNotFoundError
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from modules.strategies.infrastructure.persistence import models as _models  # noqa: F401
from modules.strategies.infrastructure.persistence.repository import StrategyRepository
from modules.strategies.infrastructure.registry.chunker_registry import chunker_registry
from modules.strategies.infrastructure.registry.embedding_registry import embedder_registry
from modules.strategies.infrastructure.registry.parser_registry import parser_registry
from modules.strategies.infrastructure.registry.reranker_registry import reranker_registry
from modules.strategies.infrastructure.registry.retriever_registry import retriever_registry
from shared.infrastructure.database.db_models import get_engine


def _ensure_tables() -> None:
    SQLModel.metadata.create_all(get_engine())  # idempotent


def validate_strategy(s: Strategy) -> None:
    """Checks every stage name against its registry. Params are not validated."""
    errors: list[str] = []
    if not s.name.strip():
        errors.append("Strategy name is required.")
    if s.parser.name != "auto_by_extension" and s.parser.name not in parser_registry.names():
        errors.append(f"Unknown parser '{s.parser.name}'.")
    for label, cfg, reg in (("chunker", s.chunker, chunker_registry),
                            ("embedder", s.embedder, embedder_registry),
                            ("retrieval", s.retrieval, retriever_registry)):
        if cfg.name not in reg.names():
            errors.append(f"Unknown {label} '{cfg.name}'. Available: {reg.names()}")
    if s.reranker and s.reranker.name not in reranker_registry.names():
        errors.append(f"Unknown reranker '{s.reranker.name}'.")
    if s.retrieval.top_k < 1:
        errors.append("top_k must be >= 1.")
    if errors:
        raise InvalidStrategyError("Invalid strategy: " + "; ".join(errors), errors)


class StrategyService:
    def __init__(self, repository: StrategyRepository | None = None):
        _ensure_tables()
        self.repository = repository or StrategyRepository()

    def create(self, name: str, parser: ParserConfig, chunker: ChunkerConfig,
               embedder: EmbeddingConfig, retrieval: RetrievalConfig,
               reranker: RerankerConfig | None = None, description: str = "") -> Strategy:
        return self.save(Strategy(name=name.strip(), description=description, parser=parser,
                                  chunker=chunker, embedder=embedder, retrieval=retrieval,
                                  reranker=reranker))

    def save(self, strategy: Strategy) -> Strategy:
        validate_strategy(strategy)
        self.repository.save(strategy)
        return strategy

    def revise(self, strategy_id: str, **changes) -> Strategy:
        strategy = self.get(strategy_id)
        if strategy.revise(**changes):
            self.save(strategy)
        return strategy

    def get(self, strategy_id: str, version: int | None = None) -> Strategy:
        s = (self.repository.get(strategy_id) if version is None
             else self.repository.get_version(strategy_id, version))
        if s is None:
            suffix = f" (version {version})" if version else ""
            raise StrategyNotFoundError(f"No strategy with id '{strategy_id}'{suffix}")
        return s

    def list(self, include_archived: bool = False) -> list[Strategy]:
        return self.repository.list(include_archived)

    def archive(self, strategy_id: str) -> Strategy:
        s = self.get(strategy_id)
        s.archive()
        self.repository.save(s)
        return s