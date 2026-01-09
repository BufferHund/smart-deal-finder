from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseOCRModel(ABC):
    """
    Abstract base class for all OCR/Multimodal models.
    """
    @abstractmethod
    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract deals from a supermarket brochure image.
        Returns a list of dicts with the following structure:
        {
            "product_name": str,
            "price": str,
            "discount": str or None,
            "unit": str or None,
            "original_price": str or None,
            "bbox": [x_min, y_min, x_max, y_max] # Normalized 0-1
        }
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns the name of the model."""
        pass
