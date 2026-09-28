from __future__ import annotations

from modules.strategies.application.services.strategy_service import StrategyService
from modules.strategies.domain.entities.strategy import Strategy


class GetStrategyQuery:
    def __init__(self, service: StrategyService | None = None):
        self.service = service or StrategyService()

    def execute(self, strategy_id: str, version: int | None = None) -> Strategy:
        return self.service.get(strategy_id, version)