from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any

_MULTILINGUAL_MIN_SHARE = 0.1


@dataclass(frozen=True)
class LanguageProfile:
    """Per-document language guesses aggregated over the corpus. Latin-script
    languages come from stopword scoring; non-Latin ones are a script-based guess
    (e.g. Devanagari -> 'hi'). Counts are documents, not characters."""

    primary_language: str = "unknown"
    confidence: float = 0.0  # share of all documents in the primary language
    language_counts: dict[str, int] = field(default_factory=dict)
    script_counts: dict[str, int] = field(default_factory=dict)

    @property
    def is_multilingual(self) -> bool:
        total = sum(self.language_counts.values())
        if total == 0:
            return False
        known = [n for lang, n in self.language_counts.items()
                 if lang != "unknown" and n / total >= _MULTILINGUAL_MIN_SHARE]
        return len(known) > 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> LanguageProfile:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in d.items() if k in names})
