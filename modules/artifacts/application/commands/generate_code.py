from __future__ import annotations

from modules.artifacts.application.services.code_generation_service import CodeGenerationService
from modules.artifacts.domain.entities.artifact import Artifact


class GenerateCodeCommand:
    """A runnable script reproducing a saved strategy (current version if version is None)."""

    def __init__(self, service: CodeGenerationService | None = None):
        self.service = service or CodeGenerationService()

    def execute(self, strategy_id: str, version: int | None = None) -> Artifact:
        return self.service.generate_strategy_code(strategy_id, version)
