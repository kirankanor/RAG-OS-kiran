from dataclasses import dataclass

from modules.strategies.domain.models.stage_config import StageConfig


@dataclass(frozen=True)
class RerankerConfig(StageConfig):
    pass