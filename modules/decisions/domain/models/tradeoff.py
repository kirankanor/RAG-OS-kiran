from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any


@dataclass(frozen=True)
class Tradeoff:
    """A runner-up that beats the winner on one factor, and what that costs overall."""

    strategy_id: str
    strategy_name: str
    factor: str
    candidate_value: str   # display strings, e.g. "1.2 s"
    winner_value: str
    statement: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Tradeoff:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})
