from __future__ import annotations

from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.entities.strategy import Strategy


class ListStrategiesQuery:
    def __init__(self, service: StrategyService | None = None):
        self.service = service or StrategyService()

    def execute(self, include_archived: bool = False) -> list[Strategy]:
        return self.service.list(include_archived)