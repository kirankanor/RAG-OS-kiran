from __future__ import annotations

from enum import Enum


class ProcessingStage(str, Enum):
    """The pipeline stage a document/chunk is currently at or has passed
    through, in ingestion order."""

    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PARSING = "parsing"
    OCR = "ocr"
    NORMALIZING = "normalizing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"

    @classmethod
    def ordered(cls) -> tuple[ProcessingStage, ...]:
        return (cls.UPLOADED, cls.VALIDATING, cls.PARSING, cls.OCR, cls.NORMALIZING,
                cls.CHUNKING, cls.EMBEDDING, cls.INDEXING, cls.COMPLETED)

    def is_before(self, other: ProcessingStage) -> bool:
        order = self.ordered()
        return order.index(self) < order.index(other)
