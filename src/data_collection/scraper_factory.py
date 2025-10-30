"""Factory for creating scrapers for different supermarkets"""

import yaml
from pathlib import Path
from typing import Optional
from .base_scraper import BaseScraper
from .aldi_scraper import AldiSuedScraper, AldiNordScraper


class ScraperFactory:
    """Factory class for creating appropriate scrapers"""

    _scrapers = {
        'aldi_sued': AldiSuedScraper,
        'aldi_nord': AldiNordScraper,
        # Add more scrapers as they are implemented
    }

    @classmethod
    def create_scraper(
        cls,
        supermarket: str,
        output_dir: str = "data/raw",
        config_path: Optional[str] = None
    ) -> Optional[BaseScraper]:
        """
        Create a scraper for the specified supermarket

        Args:
            supermarket: Name of the supermarket (e.g., 'aldi_sued')
            output_dir: Directory to save downloaded files
            config_path: Optional path to configuration file

        Returns:
            Scraper instance or None if not found
        """
        supermarket_key = supermarket.lower().replace(" ", "_")

        if supermarket_key not in cls._scrapers:
            print(f"No scraper implemented for '{supermarket}'")
            print(f"Available scrapers: {', '.join(cls._scrapers.keys())}")
            return None

        scraper_class = cls._scrapers[supermarket_key]
        return scraper_class(output_dir=output_dir)

    @classmethod
    def list_available_scrapers(cls) -> list:
        """
        Get list of available scrapers

        Returns:
            List of supermarket names
        """
        return list(cls._scrapers.keys())

    @classmethod
    def load_config(cls, config_path: str = "config/data_sources.yaml") -> dict:
        """
        Load configuration from YAML file

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary
        """
        config_file = Path(config_path)
        if not config_file.exists():
            print(f"Config file not found: {config_path}")
            return {}

        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
