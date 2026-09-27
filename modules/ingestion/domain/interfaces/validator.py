from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from shared.domain.registry import Registry


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.is_valid = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class Validator(ABC):
    """Port for a validation stage in the ingestion pipeline. Implementations
    validate different targets at different stages (raw file, extracted
    CanonicalDocument, final chunk quality) but share this contract."""

    name: str = "base"

    @abstractmethod
    def validate(self, target: Any) -> ValidationResult:
        raise NotImplementedError


validator_registry: Registry[Validator] = Registry("validator")
