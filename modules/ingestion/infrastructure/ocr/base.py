from __future__ import annotations

from abc import ABC, abstractmethod

from shared.domain.registry import Registry


class OcrEngine(ABC):
    """Extracts text from an image (e.g. a scanned page or an extracted
    Figure). Follows the same ABC+registry pattern as Parser/Chunker rather
    than a domain-owned port, since OCR strategies are infra-level backends,
    not something the domain layer needs to abstract over."""

    name: str = "base"

    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        raise NotImplementedError


ocr_registry: Registry[OcrEngine] = Registry("ocr")
