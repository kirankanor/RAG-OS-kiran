from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

TResult = TypeVar("TResult")


class Command(ABC, Generic[TResult]):
    """Optional base for the *Command classes every module already writes by hand
    (CreateStrategyCommand, UploadDocumentCommand, ...). They currently take their
    args as `execute(...)` parameters directly, which this does not change --
    subclassing is opt-in for new commands that want a typed `execute() -> TResult`
    contract; existing commands need no changes."""

    @abstractmethod
    def execute(self) -> TResult:
        raise NotImplementedError
