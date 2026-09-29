from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TResult = TypeVar("TResult")


class Query(ABC, Generic[TResult]):
    """Optional base for the *Query classes every module already writes by hand
    (GetStrategyQuery, ListDocumentsQuery, ...). Same opt-in note as Command."""

    @abstractmethod
    def execute(self) -> TResult:
        raise NotImplementedError
