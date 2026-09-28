from dataclasses import dataclass

from modules.strategies.domain.models.stage_config import StageConfig


@dataclass(frozen=True)
class EmbeddingConfig(StageConfig):
    name: str = "local_minilm"