from __future__ import annotations

from modules.ingestion.infrastructure.ocr.base import OcrEngine, ocr_registry


@ocr_registry.register("tesseract", "Local OCR via pytesseract. Requires the tesseract binary + pytesseract/Pillow.")
class TesseractOcrEngine(OcrEngine):
    name = "tesseract"

    def __init__(self, lang: str = "eng"):
        self.lang = lang

    def extract_text(self, image_path: str) -> str:
        import pytesseract
        from PIL import Image

        image = Image.open(image_path)
        return pytesseract.image_to_string(image, lang=self.lang)
