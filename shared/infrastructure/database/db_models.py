from __future__ import annotations
import json
from typing import Any
from sqlmodel import Field, Session, SQLModel, create_engine, select
from shared.config.settings import get_settings


class RunRow(SQLModel, table=True):
    __tablename__ = "runs"
    id: str = Field(primary_key=True)
    name: str = ""
    parser_name: str = ""
    parser_params: str = "{}"
    chunker_name: str = ""
    chunker_params: str = "{}"
    embedder_name: str = ""
    embedder_params: str = "{}"
    retriever_name: str = ""
    retriever_params: str = "{}"
    reranker_name: str = ""
    reranker_params: str = "{}"
    created_at: str = ""


class DocumentRow(SQLModel, table=True):
    __tablename__ = "documents"
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    source_filename: str = ""
    text: str = ""
    metadata_json: str = "{}"
    parser_name: str = ""
    created_at: str = ""


class ChunkRow(SQLModel, table=True):
    __tablename__ = "chunks"
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    document_id: str = Field(index=True)
    text: str = ""
    position: int = 0
    char_start: int = 0
    char_end: int = 0
    metadata_json: str = "{}"
    chunker_name: str = ""


class EmbeddingRow(SQLModel, table=True):
    __tablename__ = "embeddings"
    id: str = Field(primary_key=True)
    run_id: str = Field(index=True)
    chunk_id: str = Field(index=True)
    vector_json: str = ""
    dim: int = 0
    embedder_name: str = ""


class RatingRow(SQLModel, table=True):
    __tablename__ = "ratings"
    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    query: str = ""
    thumbs_up: bool = True
    note: str = ""
    created_at: str = ""


class MetricRow(SQLModel, table=True):
    __tablename__ = "metrics"
    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(index=True)
    metric_name: str = ""
    value: float = 0.0
    created_at: str = ""


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        settings.db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{settings.db_path}")
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    return Session(get_engine())


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def loads(raw: str) -> Any:
    return json.loads(raw) if raw else {}


def list_runs() -> list[RunRow]:
    with get_session() as session:
        return list(session.exec(select(RunRow).order_by(RunRow.created_at.desc())))


def get_run(run_id: str) -> RunRow | None:
    with get_session() as session:
        return session.get(RunRow, run_id)
