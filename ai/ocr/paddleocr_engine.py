"""
PakLaw AI — PaddleOCR Engine

Integrates PaddleOCR for extracting multilingual text from scanned PDF and image pages.
"""

from typing import Any, List
import numpy as np
from PIL import Image

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("ocr")


class OCRProcessor:
    """Manages PaddleOCR model instance and processes images/scanned pages."""

    def __init__(self) -> None:
        self._ocr = None

    @property
    def ocr(self):
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR as OriginalPaddleOCR
                self._ocr = OriginalPaddleOCR(
                    use_angle_cls=True,
                    lang=settings.OCR_LANG,
                    use_gpu=settings.OCR_USE_GPU,
                    show_log=False
                )
            except Exception as e:
                logger.warning("PaddleOCR initialization failed or missing: " + str(e))
                class DummyOCR:
                    def ocr(self, *args, **kwargs):
                        return None
                self._ocr = DummyOCR()
        return self._ocr

    def extract_text_from_image(self, image_path: str) -> tuple[str, float]:
        """
        Extract text from image path.
        Returns:
            Tuple of (extracted_text, average_confidence_score).
        """
        try:
            result = self.ocr.ocr(image_path, cls=True)
            if not result or not result[0]:
                return "", 0.0

            text_lines = []
            confidence_scores = []

            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                text_lines.append(text)
                confidence_scores.append(confidence)

            full_text = "\n".join(text_lines)
            avg_confidence = float(np.mean(confidence_scores)) if confidence_scores else 0.0
            
            return full_text, avg_confidence

        except Exception as e:
            logger.error("PaddleOCR execution failed", error=str(e), path=image_path)
            raise e

    def extract_text_from_pdf_page(self, pdf_page_image: Image.Image) -> tuple[str, float]:
        """
        Processes an in-memory PIL Image representing a single PDF page.
        """
        try:
            # Convert PIL to numpy array
            img_arr = np.array(pdf_page_image)
            result = self.ocr.ocr(img_arr, cls=True)
            
            if not result or not result[0]:
                return "", 0.0

            text_lines = []
            confidence_scores = []

            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                text_lines.append(text)
                confidence_scores.append(confidence)

            return "\n".join(text_lines), float(np.mean(confidence_scores)) if confidence_scores else 0.0

        except Exception as e:
            logger.error("PaddleOCR page process failure", error=str(e))
            return "", 0.0
