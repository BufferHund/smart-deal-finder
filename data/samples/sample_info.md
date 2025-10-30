# Sample Data

This directory contains sample brochure images for testing and demonstration.

## How to Use

1. Copy sample images to this directory
2. Upload them through the web interface
3. Test different OCR engines and settings

## Recommended Test Images

For testing the application, you can use:

### Option 1: Create Test Images
Use image editing software to create sample brochure-like images with:
- Product names
- Prices (e.g., "1.99 €")
- Discount labels (e.g., "-20%")
- Units (e.g., "1 kg", "500 g")

### Option 2: Download Real Brochures
Run the data collection scripts:
```bash
python src/data_collection/scraper.py --supermarket aldi_sued --max 5
```

Then copy images from `data/raw/` to this directory for easy access.

### Option 3: Screenshot Existing Brochures
Take screenshots of online supermarket brochures and save them here.

## Image Requirements

- **Format**: PNG, JPG, or JPEG
- **Size**: Recommended 1000-2000 pixels width
- **Quality**: Clear, high-resolution images work best
- **Content**: Should contain visible text (product names, prices, etc.)

## Testing Checklist

Test with images that have:
- [ ] Clear, printed text
- [ ] Various font sizes
- [ ] Different colors and backgrounds
- [ ] Multiple products per image
- [ ] Price information
- [ ] Discount labels
- [ ] Product units
- [ ] Various layouts

## Example Test Cases

### Test Case 1: Simple Layout
Single product with clear price - tests basic OCR

### Test Case 2: Multiple Products
Grid layout with several items - tests entity grouping

### Test Case 3: Complex Design
Colorful background, rotated text - tests OCR robustness

### Test Case 4: Low Quality
Scanned or low-resolution image - tests preprocessing
