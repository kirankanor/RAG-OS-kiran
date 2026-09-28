from __future__ import annotations

from modules.strategies.application.services.strategy_generator import (
    CandidateGenerator, PresetCandidateGenerator,
)
from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.entities.strategy_candidate import StrategyCandidate


class GenerateStrategiesCommand:
    """Propose candidate strategies; optionally save them all."""

    def __init__(self, service: StrategyService | None = None,
                 generator: CandidateGenerator | None = None):
        self.service = service or StrategyService()
        self.generator = generator or PresetCandidateGenerator()

    def execute(self, count: int = 3, persist: bool = False) -> list[StrategyCandidate]:
        candidates = self.generator.generate(count)
        if persist:
            for c in candidates:
                self.service.save(c.strategy)
        return candidates