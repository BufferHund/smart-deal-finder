"""
Base Extractor Interface

This module defines the abstract base class that all extractors must implement.
This design allows easy addition of new extraction methods.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import numpy as np


class BaseExtractor(ABC):
    """
    Abstract base class for all extraction methods.

    To add a new extractor:
    1. Inherit from this class
    2. Implement the required abstract methods
    3. Add to __init__.py imports
    """

    def __init__(self, name: str):
        """
        Args:
            name: Human-readable name of the extractor
        """
        self.name = name

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this extractor can be used.

        Returns:
            True if dependencies are available and extractor is ready
        """
        pass

    @abstractmethod
    def extract(self, image: np.ndarray, **kwargs) -> Dict:
        """
        Extract product deals from an image.

        Args:
            image: Image as numpy array (RGB)
            **kwargs: Extractor-specific parameters

        Returns:
            Dictionary with structure:
            {
                "deals": List[Dict],  # List of product dictionaries
                "total_products": int,
                "extraction_method": str,
                "status": str,  # "success" or "error"
                "error": str,  # Error message if status is "error"
            }
        """
        pass

    def get_info(self) -> Dict:
        """
        Get information about this extractor.

        Returns:
            Dictionary with extractor metadata
        """
        return {
            "name": self.name,
            "available": self.is_available()
        }
