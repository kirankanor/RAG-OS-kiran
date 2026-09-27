from __future__ import annotations

from collections.abc import Sequence

from modules.ingestion.domain.interfaces.validator import ValidationResult, Validator, validator_registry
from shared.domain.types import Chunk


@validator_registry.register("quality_validator", "Checks a run's chunks for emptiness, duplication, and size outliers.")
class QualityValidator(Validator):
    name = "quality_validator"

    def __init__(self, min_chunk_chars: int = 10, max_duplicate_ratio: float = 0.2):
        self.min_chunk_chars = min_chunk_chars
        self.max_duplicate_ratio = max_duplicate_ratio

    def validate(self, target: Sequence[Chunk]) -> ValidationResult:
        result = ValidationResult()
        chunks = list(target)
        if not chunks:
            result.add_error("No chunks produced.")
            return result
        short = [c for c in chunks if len(c.text.strip()) < self.min_chunk_chars]
        if short:
            result.add_warning(f"{len(short)} of {len(chunks)} chunks are shorter than {self.min_chunk_chars} chars.")
        seen, duplicates = set(), 0
        for c in chunks:
            key = c.text.strip()
            if key in seen:
                duplicates += 1
            seen.add(key)
        if duplicates / len(chunks) > self.max_duplicate_ratio:
            result.add_warning(f"High duplicate chunk ratio: {duplicates}/{len(chunks)}.")
        return result
