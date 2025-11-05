"""
Extractors Module - Extensible extraction backends

This module provides a unified interface for different extraction methods.
Add new extractors by implementing the BaseExtractor interface.
"""

from .base import BaseExtractor
from .ocr_extractor import OCRExtractor
from .gemini_extractor import GeminiExtractor
from .ollama_extractor import OllamaExtractor

__all__ = [
    'BaseExtractor',
    'OCRExtractor',
    'GeminiExtractor',
    'OllamaExtractor'
]
