from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Figure:
    """An image/chart/diagram extracted from a page."""

    caption: str = ""
    page_number: int = 0
    bbox: tuple[float, float, float, float] | None = None  # (x0, y0, x1, y1)
    image_path: str = ""       # path to extracted image on disk, if saved
    ocr_text: str = ""         # text pulled from the image via OCR, if any
