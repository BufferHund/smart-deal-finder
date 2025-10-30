#!/usr/bin/env python
"""Main script for scraping supermarket brochures"""

import argparse
import sys
from pathlib import Path
from scraper_factory import ScraperFactory


def main():
    """Main entry point for the scraper"""

    parser = argparse.ArgumentParser(
        description="Download supermarket brochures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download Aldi Süd brochures
  python scraper.py --supermarket aldi_sued

  # Download with custom output directory
  python scraper.py --supermarket aldi_nord --output /path/to/output

  # Limit number of downloads
  python scraper.py --supermarket aldi_sued --max 5

  # List available scrapers
  python scraper.py --list
        """
    )

    parser.add_argument(
        '--supermarket',
        type=str,
        help='Name of the supermarket (e.g., aldi_sued, aldi_nord)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/raw',
        help='Output directory for downloaded files (default: data/raw)'
    )

    parser.add_argument(
        '--max',
        type=int,
        help='Maximum number of brochures to download'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config/data_sources.yaml',
        help='Path to configuration file (default: config/data_sources.yaml)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available scrapers'
    )

    args = parser.parse_args()

    # List available scrapers
    if args.list:
        print("Available scrapers:")
        for scraper in ScraperFactory.list_available_scrapers():
            print(f"  - {scraper}")
        return 0

    # Check if supermarket is specified
    if not args.supermarket:
        parser.print_help()
        print("\nError: --supermarket is required (or use --list to see available scrapers)")
        return 1

    # Create scraper
    scraper = ScraperFactory.create_scraper(
        supermarket=args.supermarket,
        output_dir=args.output,
        config_path=args.config
    )

    if not scraper:
        print(f"Failed to create scraper for '{args.supermarket}'")
        return 1

    # Run scraper
    print(f"\nStarting scraper for {args.supermarket}")
    print(f"Output directory: {args.output}")
    if args.max:
        print(f"Maximum downloads: {args.max}")
    print()

    stats = scraper.run(max_downloads=args.max)

    print("\n" + "=" * 50)
    print("Scraping Summary")
    print("=" * 50)
    print(f"Total: {stats['total']}")
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print("=" * 50)

    return 0 if stats['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
