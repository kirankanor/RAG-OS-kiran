from __future__ import annotations

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.interfaces.validator import ValidationResult, Validator, validator_registry


@validator_registry.register("extraction_validator", "Checks a parsed CanonicalDocument has non-trivial extracted content.")
class ExtractionValidator(Validator):
    name = "extraction_validator"

    def __init__(self, min_chars: int = 20):
        self.min_chars = min_chars

    def validate(self, target: CanonicalDocument) -> ValidationResult:
        result = ValidationResult()
        text = target.full_text.strip()
        if not text:
            result.add_error("No text extracted from document.")
        elif len(text) < self.min_chars:
            result.add_warning(f"Extracted text is very short ({len(text)} chars).")
        if not target.pages:
            result.add_warning("Document has no pages recorded.")
        return result
