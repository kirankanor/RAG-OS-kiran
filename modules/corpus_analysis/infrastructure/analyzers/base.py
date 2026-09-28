from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from shared.domain.registry import Registry
from shared.domain.types import Document


class Analyzer(ABC):
    """Measures one aspect of a corpus. `produces` names the CorpusProfile section
    the result fills: statistics | structure | language | tables | duplicates | ocr."""

    name: str = "base"
    produces: str = ""

    @abstractmethod
    def analyze(self, documents: Sequence[Document]) -> Any:
        raise NotImplementedError


analyzer_registry: Registry[Analyzer] = Registry("analyzer")
