from __future__ import annotations

from modules.artifacts.application.services.artifact_service import ArtifactService
from modules.artifacts.domain.entities.artifact import Artifact
from modules.artifacts.domain.value_objects.artifact_type import ArtifactType
from modules.artifacts.infrastructure.generators.code_generator import (
    generate_strategy_script, script_filename,
)
from modules.strategies.application.services.strategy_service import StrategyService


class CodeGenerationService:
    def __init__(self, artifacts: ArtifactService | None = None, strategies: StrategyService | None = None):
        self.artifacts = artifacts or ArtifactService()
        self.strategies = strategies or StrategyService()

    def generate_strategy_code(self, strategy_id: str, version: int | None = None) -> Artifact:
        """A runnable .py script reproducing a saved strategy (current version if None)."""
        strategy = self.strategies.get(strategy_id, version)  # raises StrategyNotFoundError
        filename = script_filename(strategy)
        script = generate_strategy_script(strategy, filename)
        return self.artifacts.record(
            ArtifactType.CODE, f"{strategy.name} v{strategy.version.number} code", filename,
            script.encode("utf-8"), source_type="strategy", source_id=str(strategy.id))
