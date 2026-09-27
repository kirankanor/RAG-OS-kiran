from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class Document:
    id: str = field(default_factory=_new_id)
    source_filename: str = ""
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    parser_name: str = ""
    created_at: str = field(default_factory=_utcnow)


@dataclass
class Chunk:
    id: str = field(default_factory=_new_id)
    document_id: str = ""
    text: str = ""
    position: int = 0
    char_start: int = 0
    char_end: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    chunker_name: str = ""
    parent_chunk_id: str = ""


@dataclass
class EmbeddingRecord:
    id: str = field(default_factory=_new_id)
    chunk_id: str = ""
    vector: list[float] = field(default_factory=list)
    dim: int = 0
    embedder_name: str = ""


@dataclass
class RetrievalResult:
    chunk_id: str = ""
    score: float = 0.0
    rank: int = 0
    text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunConfig:
    id: str = field(default_factory=_new_id)
    name: str = ""
    parser_name: str = ""
    parser_params: dict[str, Any] = field(default_factory=dict)
    chunker_name: str = ""
    chunker_params: dict[str, Any] = field(default_factory=dict)
    embedder_name: str = ""
    embedder_params: dict[str, Any] = field(default_factory=dict)
    retriever_name: str = ""
    retriever_params: dict[str, Any] = field(default_factory=dict)
    reranker_name: str = ""
    reranker_params: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
