from __future__ import annotations

from sqlmodel import select

from modules.strategies.domain.entities.strategy import Strategy
from modules.strategies.domain.models.chunker_config import ChunkerConfig
from modules.strategies.domain.models.embedding_config import EmbeddingConfig
from modules.strategies.domain.models.parser_config import ParserConfig
from modules.strategies.domain.models.reranker_config import RerankerConfig
from modules.strategies.domain.models.retrieval_config import RetrievalConfig
from modules.strategies.domain.value_objects.strategy_id import StrategyId
from modules.strategies.domain.value_objects.strategy_version import StrategyVersion
from modules.strategies.infrastructure.persistence.models import StrategyRow, StrategyVersionRow
from shared.infrastructure.database.db_models import dumps, get_session, loads


def _config_json(s: Strategy) -> str:
    return dumps({"parser": s.parser.to_dict(), "chunker": s.chunker.to_dict(),
                  "embedder": s.embedder.to_dict(), "retrieval": s.retrieval.to_dict(),
                  "reranker": s.reranker.to_dict() if s.reranker else None})


def _build(id_, name, description, config_json, version, archived, created_at, updated_at) -> Strategy:
    c = loads(config_json)
    return Strategy(
        id=StrategyId(id_), name=name, description=description,
        parser=ParserConfig.from_dict(c["parser"]), chunker=ChunkerConfig.from_dict(c["chunker"]),
        embedder=EmbeddingConfig.from_dict(c["embedder"]),
        retrieval=RetrievalConfig.from_dict(c["retrieval"]),
        reranker=RerankerConfig.from_dict(c["reranker"]) if c.get("reranker") else None,
        version=StrategyVersion(version), is_archived=archived,
        created_at=created_at, updated_at=updated_at)


def _row_to_strategy(r: StrategyRow) -> Strategy:
    return _build(r.id, r.name, r.description, r.config_json, r.version, r.is_archived,
                  r.created_at, r.updated_at)


class StrategyRepository:
    """SQLModel-backed persistence. Concrete class (no domain port), like users."""

    def save(self, s: Strategy) -> None:
        cfg = _config_json(s)
        with get_session() as session:
            session.merge(StrategyRow(id=str(s.id), name=s.name, description=s.description,
                                      version=s.version.number, config_json=cfg,
                                      is_archived=s.is_archived, created_at=s.created_at,
                                      updated_at=s.updated_at))
            exists = session.exec(select(StrategyVersionRow).where(
                StrategyVersionRow.strategy_id == str(s.id),
                StrategyVersionRow.version == s.version.number)).first()
            if exists is None:
                session.add(StrategyVersionRow(strategy_id=str(s.id), version=s.version.number,
                                               name=s.name, description=s.description,
                                               config_json=cfg, created_at=s.updated_at))
            session.commit()

    def get(self, strategy_id: str) -> Strategy | None:
        with get_session() as session:
            row = session.get(StrategyRow, strategy_id)
        return _row_to_strategy(row) if row else None

    def get_version(self, strategy_id: str, number: int) -> Strategy | None:
        with get_session() as session:
            v = session.exec(select(StrategyVersionRow).where(
                StrategyVersionRow.strategy_id == strategy_id,
                StrategyVersionRow.version == number)).first()
            cur = session.get(StrategyRow, strategy_id)
        if v is None or cur is None:
            return None
        return _build(strategy_id, v.name, v.description, v.config_json, v.version,
                      cur.is_archived, cur.created_at, v.created_at)

    def list_versions(self, strategy_id: str) -> list[int]:
        with get_session() as session:
            rows = session.exec(select(StrategyVersionRow).where(
                StrategyVersionRow.strategy_id == strategy_id).order_by(StrategyVersionRow.version))
            return [r.version for r in rows]

    def list(self, include_archived: bool = False) -> list[Strategy]:
        with get_session() as session:
            stmt = select(StrategyRow).order_by(StrategyRow.created_at.desc())
            if not include_archived:
                stmt = stmt.where(StrategyRow.is_archived == False)  # noqa: E712
            return [_row_to_strategy(r) for r in session.exec(stmt)]