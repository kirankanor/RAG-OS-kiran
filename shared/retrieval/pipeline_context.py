from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from shared.domain.types import Chunk


@dataclass
class Candidate:
    chunk: Chunk
    vector: list[float] | None = None
    score: float = 0.0
    source_step: str = ""
    parent_text: str = ""


@dataclass
class PipelineContext:
    query: str
    query_vector: list[float] | None
    all_chunks: list[Chunk]
    all_vectors: dict[str, list[float]]
    candidates: list[Candidate] = field(default_factory=list)
    top_k: int = 5
    scratch: dict[str, Any] = field(default_factory=dict)

    def chunks_by_id(self) -> dict[str, Chunk]:
        return {c.id: c for c in self.all_chunks}
