"""
Model Registry - Unified model management system

This module provides a centralized registry for all extraction models.
Easy to add new models without modifying the application code.
"""

from typing import Dict, List, Type
from .base import BaseExtractor


class ModelRegistry:
    """
    Centralized registry for all extraction models.

    Models are automatically discovered and registered.
    The application queries this registry to get available models.
    """

    def __init__(self):
        self._models: Dict[str, Type[BaseExtractor]] = {}
        self._instances: Dict[str, BaseExtractor] = {}

    def register(self, name: str, extractor_class: Type[BaseExtractor]):
        """
        Register a new extractor model.

        Args:
            name: Unique identifier for the model
            extractor_class: The extractor class (not instance)
        """
        self._models[name] = extractor_class

    def get(self, name: str) -> BaseExtractor:
        """
        Get an instance of a registered extractor.

        Args:
            name: Model identifier

        Returns:
            Extractor instance
        """
        if name not in self._instances:
            if name not in self._models:
                raise ValueError(f"Model '{name}' not registered")
            self._instances[name] = self._models[name]()
        return self._instances[name]

    def list_available(self) -> List[Dict]:
        """
        List all available (ready to use) models.

        Returns:
            List of model info dictionaries
        """
        available = []
        for name, extractor_class in self._models.items():
            # Create temporary instance to check availability
            instance = extractor_class()
            if instance.is_available():
                info = instance.get_info()
                info['id'] = name
                available.append(info)
        return available

    def list_all(self) -> List[Dict]:
        """
        List all registered models (whether available or not).

        Returns:
            List of model info dictionaries
        """
        all_models = []
        for name, extractor_class in self._models.items():
            instance = extractor_class()
            info = instance.get_info()
            info['id'] = name
            all_models.append(info)
        return all_models


# Global registry instance
registry = ModelRegistry()


def register_model(name: str):
    """
    Decorator for easy model registration.

    Usage:
        @register_model("my_model")
        class MyExtractor(BaseExtractor):
            pass
    """
    def decorator(cls):
        registry.register(name, cls)
        return cls
    return decorator
