from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from modules.strategies.domain.models.stage_config import StageConfig


@dataclass(frozen=True)
class RetrievalConfig(StageConfig):
    name: str = "faiss_flat_l2"
    top_k: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "top_k": self.top_k}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetrievalConfig:
        return cls(name=data.get("name", "faiss_flat_l2"), params=dict(data.get("params", {})),
                   top_k=data.get("top_k", 5))