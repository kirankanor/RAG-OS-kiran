from __future__ import annotations


class StrategyError(Exception):
    """Base exception for all strategies-domain errors."""


class InvalidStrategyError(StrategyError):
    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


class StrategyNotFoundError(StrategyError):
    pass