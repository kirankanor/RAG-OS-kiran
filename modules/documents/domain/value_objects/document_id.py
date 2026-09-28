from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DocumentId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("DocumentId cannot be empty.")

    @classmethod
    def new(cls) -> DocumentId:
        return cls(uuid.uuid4().hex[:12])

    def __str__(self) -> str:
        return self.value
