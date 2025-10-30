"""Base scraper class for supermarket brochure collection"""

import os
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for supermarket brochure scrapers"""

    def __init__(
        self,
        supermarket_name: str,
        base_url: str,
        output_dir: str = "data/raw",
        user_agent: Optional[str] = None,
        timeout: int = 30,
        delay: int = 2
    ):
        """
        Initialize the scraper

        Args:
            supermarket_name: Name of the supermarket
            base_url: Base URL for the supermarket website
            output_dir: Directory to save downloaded files
            user_agent: User agent string for requests
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
        """
        self.supermarket_name = supermarket_name
        self.base_url = base_url
        self.output_dir = Path(output_dir) / supermarket_name.lower().replace(" ", "_")
        self.timeout = timeout
        self.delay = delay

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set up session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        logger.info(f"Initialized scraper for {supermarket_name}")

    @abstractmethod
    def get_brochure_urls(self) -> List[str]:
        """
        Get list of brochure URLs to download

        Returns:
            List of URLs
        """
        pass

    @abstractmethod
    def download_brochure(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a brochure from URL

        Args:
            url: URL of the brochure
            filename: Optional custom filename

        Returns:
            Path to downloaded file or None if failed
        """
        pass

    def fetch_page(self, url: str) -> Optional[requests.Response]:
        """
        Fetch a webpage with error handling

        Args:
            url: URL to fetch

        Returns:
            Response object or None if failed
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            time.sleep(self.delay)  # Be nice to servers
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def save_file(self, content: bytes, filename: str) -> Optional[str]:
        """
        Save content to file

        Args:
            content: File content in bytes
            filename: Name of the file

        Returns:
            Path to saved file or None if failed
        """
        try:
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(content)
            logger.info(f"Saved: {filepath}")
            return str(filepath)
        except IOError as e:
            logger.error(f"Error saving file {filename}: {e}")
            return None

    def generate_filename(self, extension: str = "pdf", **kwargs) -> str:
        """
        Generate standardized filename

        Args:
            extension: File extension
            **kwargs: Additional metadata (date, page, etc.)

        Returns:
            Generated filename
        """
        date_str = kwargs.get('date', datetime.now().strftime('%Y%m%d'))
        page = kwargs.get('page', '')

        parts = [
            self.supermarket_name.lower().replace(" ", "_"),
            date_str
        ]

        if page:
            parts.append(f"page{page}")

        return f"{'_'.join(parts)}.{extension}"

    def run(self, max_downloads: Optional[int] = None) -> Dict[str, int]:
        """
        Run the scraper to download brochures

        Args:
            max_downloads: Maximum number of brochures to download

        Returns:
            Dictionary with download statistics
        """
        logger.info(f"Starting scraper for {self.supermarket_name}")

        urls = self.get_brochure_urls()
        if max_downloads:
            urls = urls[:max_downloads]

        stats = {
            'total': len(urls),
            'success': 0,
            'failed': 0
        }

        for i, url in enumerate(urls, 1):
            logger.info(f"Processing {i}/{len(urls)}: {url}")
            result = self.download_brochure(url)

            if result:
                stats['success'] += 1
            else:
                stats['failed'] += 1

        logger.info(f"Scraping completed. Success: {stats['success']}, Failed: {stats['failed']}")
        return stats
