from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from modules.strategies.domain.value_objects.strategy_id import StrategyId
from modules.strategies.domain.value_objects.strategy_version import StrategyVersion
from shared.domain.types import RunConfig


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


_REVISABLE = ("name", "description", "parser", "chunker", "embedder", "retrieval", "reranker")


@dataclass
class Strategy:
    """A saved, named, versioned parser+chunker+embedder+retrieval(+reranker) config."""

    id: StrategyId = field(default_factory=StrategyId.new)
    name: str = ""
    description: str = ""
    parser: ParserConfig = field(default_factory=ParserConfig)
    chunker: ChunkerConfig = field(default_factory=ChunkerConfig)
    embedder: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    reranker: RerankerConfig | None = None
    version: StrategyVersion = field(default_factory=StrategyVersion)
    is_archived: bool = False
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def revise(self, **changes) -> bool:
        """Apply changes; bumps the version only if something actually changed."""
        unknown = set(changes) - set(_REVISABLE)
        if unknown:
            raise ValueError(f"Cannot revise fields: {sorted(unknown)}")
        changed = {k: v for k, v in changes.items() if getattr(self, k) != v}
        if not changed:
            return False
        for k, v in changed.items():
            setattr(self, k, v)
        self.version = self.version.bumped()
        self.updated_at = _utcnow()
        return True

    def archive(self) -> None:
        self.is_archived = True
        self.updated_at = _utcnow()

    def to_run_config(self) -> RunConfig:
        """Bridge to the working pipeline (shared.domain.types.RunConfig)."""
        rr = self.reranker
        return RunConfig(
            name=f"{self.name} {self.version}", parser_name=self.parser.name,
            parser_params=dict(self.parser.params), chunker_name=self.chunker.name,
            chunker_params=dict(self.chunker.params), embedder_name=self.embedder.name,
            embedder_params=dict(self.embedder.params), retriever_name=self.retrieval.name,
            retriever_params=dict(self.retrieval.params),
            reranker_name=rr.name if rr else "", reranker_params=dict(rr.params) if rr else {},
        )