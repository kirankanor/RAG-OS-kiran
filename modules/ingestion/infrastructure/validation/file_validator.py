from __future__ import annotations

from pathlib import Path

from modules.ingestion.domain.interfaces.validator import ValidationResult, Validator, validator_registry
from modules.ingestion.infrastructure.parsers.base import DEFAULT_STRATEGY_BY_EXTENSION


@validator_registry.register("file_validator", "Checks a raw upload exists, is non-empty, and has a supported extension.")
class FileValidator(Validator):
    name = "file_validator"

    def __init__(self, max_size_bytes: int = 50 * 1024 * 1024):
        self.max_size_bytes = max_size_bytes

    def validate(self, target) -> ValidationResult:
        result = ValidationResult()
        path = Path(target)
        if not path.exists():
            result.add_error(f"File not found: {path}")
            return result
        if not path.is_file():
            result.add_error(f"Not a file: {path}")
            return result
        ext = path.suffix.lower()
        if ext not in DEFAULT_STRATEGY_BY_EXTENSION:
            result.add_error(f"Unsupported file extension: '{ext}'")
        size = path.stat().st_size
        if size == 0:
            result.add_error("File is empty.")
        elif size > self.max_size_bytes:
            result.add_error(f"File exceeds max size of {self.max_size_bytes} bytes ({size} bytes).")
        return result
