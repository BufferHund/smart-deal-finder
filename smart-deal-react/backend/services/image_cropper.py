"""
Image Cropping Service
Crops product images from flyer pages using bbox coordinates.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List
from PIL import Image

# Output directory for cropped images
CROPS_DIR = Path(__file__).parent.parent.parent / "frontend" / "public" / "crops"


def ensure_crops_dir(store: str) -> Path:
    """Ensure the crops directory exists for a store."""
    store_dir = CROPS_DIR / store.lower().replace(" ", "_")
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def crop_product_image(
    source_image_path: str,
    bbox: List[float],
    store: str,
    product_name: str
) -> Optional[str]:
    """
    Crop a product image from a flyer page using normalized bbox coordinates.
    
    Args:
        source_image_path: Path to the source flyer image
        bbox: [x_min, y_min, x_max, y_max] normalized coordinates (0-1)
        store: Store name for organizing output
        product_name: Product name for generating unique filename
    
    Returns:
        Relative URL path to the cropped image, or None if failed
    """
    try:
        if not os.path.exists(source_image_path):
            print(f"  ⚠️ Source image not found: {source_image_path}")
            return None
        
        if not bbox or len(bbox) != 4:
            print(f"  ⚠️ Invalid bbox: {bbox}")
            return None
        
        # Open source image
        with Image.open(source_image_path) as img:
            width, height = img.size
            
            # Convert normalized bbox to pixel coordinates
            x_min = int(bbox[0] * width)
            y_min = int(bbox[1] * height)
            x_max = int(bbox[2] * width)
            y_max = int(bbox[3] * height)
            
            # Validate coordinates
            if x_min >= x_max or y_min >= y_max:
                print(f"  ⚠️ Invalid bbox dimensions: {bbox}")
                return None
            
            # Crop the image
            cropped = img.crop((x_min, y_min, x_max, y_max))
            
            # Generate unique filename based on content
            hash_input = f"{source_image_path}_{bbox}_{product_name}"
            file_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
            
            # Ensure output directory exists
            store_dir = ensure_crops_dir(store)
            
            # Save as WebP for smaller file size
            output_filename = f"{file_hash}.webp"
            output_path = store_dir / output_filename
            
            # Resize if too large (max 400px width)
            if cropped.width > 400:
                ratio = 400 / cropped.width
                new_size = (400, int(cropped.height * ratio))
                cropped = cropped.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (for WebP compatibility)
            if cropped.mode in ('RGBA', 'P'):
                cropped = cropped.convert('RGB')
            
            # Save with good quality
            cropped.save(output_path, 'WEBP', quality=85)
            
            # Return relative URL path (for frontend)
            store_slug = store.lower().replace(" ", "_")
            return f"/crops/{store_slug}/{output_filename}"
            
    except Exception as e:
        print(f"  ⚠️ Error cropping image: {e}")
        return None


def batch_crop_from_annotations(
    annotations_dir: str,
    images_dir: str,
    store: str
) -> dict:
    """
    Batch process annotations to crop all product images.
    
    Args:
        annotations_dir: Directory containing annotation JSON files
        images_dir: Directory containing source flyer images
        store: Store name
    
    Returns:
        Dict mapping product_name to image_url
    """
    import json
    from pathlib import Path
    
    results = {}
    annotations_path = Path(annotations_dir)
    images_path = Path(images_dir)
    
    for json_file in annotations_path.glob("*.json"):
        # Find corresponding image
        image_name = json_file.stem + ".png"
        image_path = images_path / image_name
        
        if not image_path.exists():
            # Try jpg
            image_name = json_file.stem + ".jpg"
            image_path = images_path / image_name
        
        if not image_path.exists():
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                deals = json.load(f)
            
            if not deals:
                continue
                
            for deal in deals:
                product_name = deal.get('product_name', '')
                bbox = deal.get('bbox')
                
                if product_name and bbox:
                    image_url = crop_product_image(
                        str(image_path),
                        bbox,
                        store,
                        product_name
                    )
                    if image_url:
                        results[product_name] = image_url
                        
        except Exception as e:
            print(f"  ⚠️ Error processing {json_file.name}: {e}")
    
    return results


if __name__ == "__main__":
    # Test cropping
    test_image = Path(__file__).parent.parent.parent / "data" / "images_uniform" / "rewe" / "rewe_10112025_page_1.png"
    test_bbox = [0.12, 0.27, 0.36, 0.47]  # Monster Energy Drink
    
    if test_image.exists():
        result = crop_product_image(str(test_image), test_bbox, "REWE", "Monster Energy")
        print(f"Test result: {result}")
    else:
        print(f"Test image not found: {test_image}")
