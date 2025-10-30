"""Scraper for Aldi Süd and Aldi Nord brochures"""

import re
from typing import List, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, logger


class AldiSuedScraper(BaseScraper):
    """Scraper for Aldi Süd brochures"""

    def __init__(self, output_dir: str = "data/raw"):
        super().__init__(
            supermarket_name="aldi_sued",
            base_url="https://prospekt.aldi-sued.de",
            output_dir=output_dir
        )
        # Current week and year - can be made configurable
        import datetime
        self.current_week = datetime.datetime.now().isocalendar()[1]
        self.current_year = datetime.datetime.now().year

    def get_brochure_urls(self) -> List[str]:
        """
        Get Aldi Süd brochure URLs

        Returns:
            List of PDF URLs
        """
        # Aldi Süd URL pattern: https://prospekt.aldi-sued.de/kw{week}-{year}-op-mp/page/{page}
        # We need to explore the page to find PDF links

        urls = []
        base_page_url = f"{self.base_url}/kw{self.current_week:02d}-{str(self.current_year)[2:]}-op-mp/page/1"

        logger.info(f"Exploring Aldi Süd brochure at {base_page_url}")

        response = self.fetch_page(base_page_url)
        if not response:
            logger.warning("Could not fetch Aldi Süd page")
            return urls

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for PDF download links
        # This might need adjustment based on actual page structure
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))

        for link in pdf_links:
            href = link.get('href')
            if href:
                if not href.startswith('http'):
                    href = self.base_url + href
                urls.append(href)

        # If no direct PDF links found, we might need to scrape images from pages
        if not urls:
            logger.info("No direct PDF links found, will need to scrape page images")
            # Add page URLs for image scraping
            # Try to find the total number of pages
            page_links = soup.find_all('a', href=re.compile(r'/page/\d+'))
            max_page = 1
            for link in page_links:
                page_match = re.search(r'/page/(\d+)', link.get('href', ''))
                if page_match:
                    max_page = max(max_page, int(page_match.group(1)))

            for page in range(1, max_page + 1):
                page_url = f"{self.base_url}/kw{self.current_week:02d}-{str(self.current_year)[2:]}-op-mp/page/{page}"
                urls.append(page_url)

        logger.info(f"Found {len(urls)} URLs for Aldi Süd")
        return urls

    def download_brochure(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download Aldi Süd brochure

        Args:
            url: URL of the brochure
            filename: Optional custom filename

        Returns:
            Path to downloaded file
        """
        response = self.fetch_page(url)
        if not response:
            return None

        # Determine if this is a PDF or a page to scrape
        if url.endswith('.pdf'):
            # Direct PDF download
            if not filename:
                filename = self.generate_filename('pdf')

            return self.save_file(response.content, filename)
        else:
            # Scrape page for images
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the main brochure image
            # This selector might need adjustment based on actual page structure
            img_tags = soup.find_all('img', class_=re.compile(r'brochure|flyer|page', re.I))

            if not img_tags:
                # Try to find any large images
                img_tags = soup.find_all('img')

            for img in img_tags:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    if not img_url.startswith('http'):
                        img_url = self.base_url + img_url

                    # Download the image
                    img_response = self.fetch_page(img_url)
                    if img_response:
                        # Determine extension from URL or content-type
                        ext = 'jpg'
                        if '.png' in img_url.lower():
                            ext = 'png'
                        elif '.webp' in img_url.lower():
                            ext = 'webp'

                        if not filename:
                            page_match = re.search(r'/page/(\d+)', url)
                            page = page_match.group(1) if page_match else '1'
                            filename = self.generate_filename(ext, page=page)

                        return self.save_file(img_response.content, filename)

            logger.warning(f"No images found on page {url}")
            return None


class AldiNordScraper(BaseScraper):
    """Scraper for Aldi Nord brochures"""

    def __init__(self, output_dir: str = "data/raw"):
        super().__init__(
            supermarket_name="aldi_nord",
            base_url="https://www.aldi-nord.de",
            output_dir=output_dir
        )

    def get_brochure_urls(self) -> List[str]:
        """
        Get Aldi Nord brochure URLs

        Returns:
            List of PDF URLs
        """
        urls = []
        brochure_page = f"{self.base_url}/prospekte/aldi-aktuell.html"

        logger.info(f"Exploring Aldi Nord brochure at {brochure_page}")

        response = self.fetch_page(brochure_page)
        if not response:
            logger.warning("Could not fetch Aldi Nord page")
            return urls

        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for PDF download links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))

        for link in pdf_links:
            href = link.get('href')
            if href:
                if not href.startswith('http'):
                    href = self.base_url + href
                urls.append(href)

        logger.info(f"Found {len(urls)} URLs for Aldi Nord")
        return urls

    def download_brochure(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download Aldi Nord brochure

        Args:
            url: URL of the brochure
            filename: Optional custom filename

        Returns:
            Path to downloaded file
        """
        response = self.fetch_page(url)
        if not response:
            return None

        if not filename:
            filename = self.generate_filename('pdf')

        return self.save_file(response.content, filename)
