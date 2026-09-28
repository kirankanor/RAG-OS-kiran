from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class DocumentHash:
    """SHA-256 of a file's raw bytes (lowercase hex). Identifies content, not filename."""

    value: str

    def __post_init__(self) -> None:
        if not _SHA256_RE.fullmatch(self.value):
            raise ValueError("DocumentHash must be a 64-character lowercase hex SHA-256 digest.")

    @classmethod
    def from_bytes(cls, data: bytes) -> DocumentHash:
        return cls(hashlib.sha256(data).hexdigest())

    @property
    def short(self) -> str:
        return self.value[:12]

    def __str__(self) -> str:
        return self.value
