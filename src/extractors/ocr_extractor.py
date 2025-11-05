"""
OCR-based Extractor

Simple and fast extraction using OCR + pattern matching.
"""

import sys
from pathlib import Path
import numpy as np
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.base import BaseExtractor
from extractors.model_registry import register_model


@register_model("ocr_tesseract")
class TesseractExtractor(BaseExtractor):
    """Tesseract OCR-based extractor"""

    def __init__(self):
        super().__init__("Tesseract OCR")

    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

    def extract(self, image: np.ndarray, **kwargs) -> Dict:
        """
        Extract deals using Tesseract OCR

        Args:
            image: Image as numpy array
            **kwargs: Optional parameters (ocr_engine, extraction_method)

        Returns:
            Extraction result dictionary
        """
        try:
            # Import OCR matcher from app directory
            from app.ocr_deal_matcher import extract_deals_from_image

            # Extract using OCR
            result = extract_deals_from_image(
                image,
                ocr_engine=kwargs.get("ocr_engine", "tesseract"),
                extraction_method=kwargs.get("extraction_method", "advanced_region")
            )

            return result

        except Exception as e:
            return {
                "deals": [],
                "total_products": 0,
                "extraction_method": self.name,
                "status": "error",
                "error": str(e)
            }

    def get_info(self) -> Dict:
        """Get extractor information"""
        info = super().get_info()
        info.update({
            "type": "ocr",
            "accuracy": 0.90,
            "speed": "fast",
            "cost": "free"
        })
        return info


@register_model("ocr_paddle")
class PaddleOCRExtractor(BaseExtractor):
    """PaddleOCR-based extractor"""

    def __init__(self):
        super().__init__("PaddleOCR")

    def is_available(self) -> bool:
        """Check if PaddleOCR is available"""
        try:
            import paddleocr
            return True
        except:
            return False

    def extract(self, image: np.ndarray, **kwargs) -> Dict:
        """Extract deals using PaddleOCR"""
        try:
            from app.ocr_deal_matcher import extract_deals_from_image

            result = extract_deals_from_image(
                image,
                ocr_engine="paddle",
                extraction_method=kwargs.get("extraction_method", "advanced_region")
            )

            return result

        except Exception as e:
            return {
                "deals": [],
                "total_products": 0,
                "extraction_method": self.name,
                "status": "error",
                "error": str(e)
            }

    def get_info(self) -> Dict:
        """Get extractor information"""
        info = super().get_info()
        info.update({
            "type": "ocr",
            "accuracy": 0.92,
            "speed": "medium",
            "cost": "free"
        })
        return info
