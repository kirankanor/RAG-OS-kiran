from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Optional explicit success/failure wrapper for a command/query outcome, as an
    alternative to letting the module's own exception types propagate (the pattern every
    module currently uses, e.g. StrategyNotFoundError). Existing commands/queries are
    unaffected; use this only where returning-not-raising is preferred."""

    ok: bool
    value: T | None = None
    error: str = ""

    @classmethod
    def success(cls, value: T) -> Result[T]:
        return cls(True, value=value)

    @classmethod
    def failure(cls, error: str) -> Result[T]:
        return cls(False, error=error)

    def unwrap(self) -> T:
        if not self.ok:
            raise ValueError(self.error or "Result is a failure with no error message.")
        return self.value  # type: ignore[return-value]
