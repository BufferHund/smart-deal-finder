#!/usr/bin/env python3
"""
Enhanced Import Script for Labeled Annotation Data.

This script:
1. Clears existing deals from the database
2. Imports annotated JSON files from data/images_uniform/*_annotated/
3. Crops product images using bbox coordinates
4. Auto-classifies products into categories
5. Sets valid_until dates (default: next Sunday)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from db import db
from services.image_cropper import crop_product_image
from services.category_classifier import classify_product

# Store name mapping
STORE_MAP = {
    'rewe': 'REWE',
    'aldisued': 'Aldi Süd',
    'edeka': 'EDEKA',
    'kaufland': 'Kaufland',
    'netto': 'Netto',
    'penny': 'Penny',
    'rossmann': 'Rossmann',
}


def get_store_name(folder_name: str) -> str:
    """Extract store name from folder (e.g., 'rewe_annotated' -> 'REWE')"""
    folder_base = folder_name.replace('_annotated', '').lower()
    return STORE_MAP.get(folder_base, folder_base.title())


def get_next_sunday() -> datetime:
    """Get the date of next Sunday."""
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    if days_until_sunday == 0:
        days_until_sunday = 7  # Next Sunday, not today
    return today + timedelta(days=days_until_sunday)


def clear_deals():
    """Clear all existing deals from the database"""
    try:
        db.execute_query("DELETE FROM deals")
        db.execute_query("DELETE FROM uploads")
        print("✅ Cleared all existing deals and uploads")
    except Exception as e:
        print(f"❌ Error clearing deals: {e}")
        raise


def add_discount_column():
    """Add discount column to deals table if not exists"""
    try:
        db.execute_query("""
            ALTER TABLE deals ADD COLUMN IF NOT EXISTS discount VARCHAR(100)
        """)
        print("✅ Ensured discount column exists")
    except Exception as e:
        # Column might already exist
        pass


def import_annotations(data_dir: str, use_ai_classifier: bool = True):
    """Import all annotation files from the data directory"""
    
    base_path = Path(data_dir) / "images_uniform"
    if not base_path.exists():
        print(f"❌ Data directory not found: {base_path}")
        return 0
    
    # Find all annotated directories
    annotated_dirs = list(base_path.glob("*_annotated"))
    print(f"📂 Found {len(annotated_dirs)} annotated directories")
    
    # Default valid_until
    valid_until = get_next_sunday()
    print(f"📅 Valid until: {valid_until.strftime('%Y-%m-%d')}")
    
    total_deals = 0
    total_images = 0
    
    for ann_dir in sorted(annotated_dirs):
        store_name = get_store_name(ann_dir.name)
        store_folder = ann_dir.name.replace('_annotated', '')
        images_dir = base_path / store_folder
        
        json_files = list(ann_dir.glob("*.json"))
        
        print(f"\n📁 Processing {store_name} ({len(json_files)} files)...")
        
        store_deals = 0
        store_images = 0
        
        for json_file in sorted(json_files):
            # Find corresponding image
            image_name = json_file.stem + ".png"
            image_path = images_dir / image_name
            
            if not image_path.exists():
                image_name = json_file.stem + ".jpg"
                image_path = images_dir / image_name
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    deals = json.load(f)
                
                if not deals:
                    continue
                    
                for deal in deals:
                    product_name = deal.get('product_name', 'Unknown')
                    
                    # Parse price
                    price_str = deal.get('price', '0')
                    try:
                        price = float(str(price_str).replace(',', '.').replace('€', '').strip())
                    except (ValueError, AttributeError):
                        price = 0.0
                    
                    # Get discount
                    discount = deal.get('discount')
                    if discount:
                        discount = str(discount)
                    
                    # Crop image if bbox exists
                    image_url = None
                    bbox = deal.get('bbox')
                    if bbox and image_path.exists():
                        image_url = crop_product_image(
                            str(image_path),
                            bbox,
                            store_name,
                            product_name
                        )
                        if image_url:
                            store_images += 1
                    
                    # Classify category
                    category = classify_product(product_name, use_ai_fallback=use_ai_classifier)
                    
                    # Insert into database
                    db.execute_query(
                        """
                        INSERT INTO deals (product_name, price, original_price, unit, store, 
                                          confidence, source, category, image_url, valid_until, discount)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            product_name,
                            price,
                            deal.get('original_price'),
                            deal.get('unit'),
                            store_name,
                            1.0,  # Human-labeled = 100% confidence
                            'labeled',
                            category,
                            image_url,
                            valid_until,
                            discount
                        )
                    )
                    store_deals += 1
                    
            except json.JSONDecodeError as e:
                print(f"  ⚠️ Invalid JSON in {json_file.name}: {e}")
            except Exception as e:
                print(f"  ⚠️ Error processing {json_file.name}: {e}")
        
        print(f"  ✅ Imported {store_deals} deals, {store_images} images from {store_name}")
        total_deals += store_deals
        total_images += store_images
    
    print(f"\n🎉 Total: Imported {total_deals} deals with {total_images} images from {len(annotated_dirs)} stores")
    return total_deals


def main():
    print("=" * 60)
    print("SmartDeal Enhanced Data Import Tool")
    print("=" * 60)
    
    # Get data directory (relative to this script)
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        sys.exit(1)
    
    print(f"📂 Data directory: {data_dir}")
    
    # Check for AI fallback flag
    use_ai = "--no-ai" not in sys.argv
    if not use_ai:
        print("🔧 AI classifier disabled (keyword matching only)")
    
    print("\n⚠️  This will DELETE all existing deals and import fresh data.")
    
    # Ensure schema updates
    add_discount_column()
    
    # Clear and import
    clear_deals()
    total = import_annotations(str(data_dir), use_ai_classifier=use_ai)
    
    print(f"\n✅ Import complete! {total} deals now in database.")
    print("📸 Cropped images saved to: frontend/public/crops/")


if __name__ == "__main__":
    main()
