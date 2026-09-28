from dataclasses import dataclass

from modules.strategies.domain.models.stage_config import StageConfig


@dataclass(frozen=True)
class ParserConfig(StageConfig):
    name: str = "auto_by_extension"