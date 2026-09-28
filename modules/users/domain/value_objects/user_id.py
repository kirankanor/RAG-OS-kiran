from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("UserId cannot be empty.")

    @classmethod
    def new(cls) -> UserId:
        return cls(uuid.uuid4().hex[:12])

    def __str__(self) -> str:
        return self.value
