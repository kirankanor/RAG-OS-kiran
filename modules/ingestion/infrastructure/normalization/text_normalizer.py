from __future__ import annotations

import re
import unicodedata

from modules.ingestion.domain.entities.canonical_document import CanonicalDocument
from modules.ingestion.domain.interfaces.normalizer import Normalizer, normalizer_registry

_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_BLANK_LINE_RE = re.compile(r"\n{3,}")


@normalizer_registry.register("text_normalizer", "Normalizes unicode, whitespace, and blank lines in block text.")
class TextNormalizer(Normalizer):
    name = "text_normalizer"

    def normalize(self, document: CanonicalDocument) -> CanonicalDocument:
        for page in document.pages:
            for block in page.blocks:
                if not block.text:
                    continue
                text = unicodedata.normalize("NFKC", block.text)
                text = _MULTI_SPACE_RE.sub(" ", text)
                text = _MULTI_BLANK_LINE_RE.sub("\n\n", text)
                block.text = text.strip()
        return document
