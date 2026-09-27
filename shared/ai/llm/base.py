from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.registry import Registry
from shared.domain.types import RetrievalResult


class Generator(ABC):
    """Interface every answer-generation (synthesis) strategy must implement.
    Takes a user query + the chunks a retrieval pipeline already returned, and
    produces a final natural-language answer grounded in that context."""

    name: str = "base"

    @abstractmethod
    def generate(self, query: str, results: list[RetrievalResult]) -> str:
        """Synthesize a final answer to `query` using `results` as context."""
        raise NotImplementedError


generator_registry: Registry[Generator] = Registry("generator")
