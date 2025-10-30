# SmartDeal Web Application Guide

Complete guide for using the SmartDeal web application.

## Table of Contents
1. [Getting Started](#getting-started)
2. [User Interface](#user-interface)
3. [Features](#features)
4. [Workflow](#workflow)
5. [Tips & Tricks](#tips--tricks)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
- Python 3.8+
- Required packages installed (`pip install -r requirements.txt`)
- (Optional) Tesseract OCR for better accuracy

### Launching the App

**Option 1: Using the launch script**
```bash
./run_app.sh
```

**Option 2: Using Streamlit directly**
```bash
streamlit run src/app/enhanced_app.py
```

**Option 3: Using the simple version**
```bash
streamlit run src/app/app.py
```

The application will open in your browser at `http://localhost:8501`

## User Interface

### Layout

The app consists of:
- **Sidebar**: Configuration and settings
- **Main Area**: Four tabs for different functions
- **Footer**: Version and credits

### Sidebar Options

#### OCR Engine
- **PaddleOCR**: Best accuracy, requires GPU for optimal speed
- **Tesseract**: Good balance, system installation required
- **EasyOCR**: Easy to use, no additional setup

#### Preprocessing
- **Enable**: Applies denoising, thresholding (recommended)
- **Disable**: Uses original image (for high-quality scans)

#### Confidence Threshold
- **Range**: 0.0 - 1.0
- **Recommended**: 0.5-0.7
- **Lower**: More detections, more noise
- **Higher**: Fewer detections, higher accuracy

#### Display Options
- **Show Bounding Boxes**: Visual boxes around detected text
- **Show Text Labels**: Display extracted text on image
- **Show Confidence Scores**: Include confidence percentages

### Main Tabs

#### 1. 📤 Upload & Process
**Purpose**: Upload and process brochure images

**Features**:
- File upload (PNG, JPG, JPEG)
- Side-by-side comparison (original vs processed)
- One-click processing
- File size display
- Reset option

**Workflow**:
1. Click "Browse files" or drag & drop
2. Preview your image
3. Adjust settings in sidebar
4. Click "Extract Information"
5. View results with bounding boxes

#### 2. 🔍 Extracted Data
**Purpose**: View and export all detected text

**Features**:
- Summary metrics (text boxes, products, prices, discounts)
- Entity breakdown by type
- Tabbed interface for each entity category
- Data tables with confidence scores
- Export to CSV/JSON

**Entity Types**:
- **Products**: Detected product names
- **Prices**: Monetary values
- **Discounts**: Percentage off
- **Units**: Quantities and measurements
- **Dates**: Validity periods

**Actions**:
- Filter and sort data
- Export individual entity types
- Download all data at once

#### 3. 📊 Deals Analysis
**Purpose**: View structured deal information

**Features**:
- Automatic deal grouping
- Product-price-discount linking
- Expandable deal cards
- Export deals to CSV/JSON

**Deal Components**:
- Product name
- Price (in €)
- Discount percentage
- Unit information

**How it Works**:
The app automatically groups nearby entities using spatial proximity to create complete deal records.

#### 4. 📚 History
**Purpose**: Track processing history

**Features**:
- List of all processed files
- Timestamp and metadata
- Processing statistics
- Clear history option

**Information Tracked**:
- Timestamp
- Filename
- OCR engine used
- Number of text boxes detected
- Number of deals identified

## Features

### OCR Processing

The app supports three OCR engines:

1. **PaddleOCR**
   - Pros: High accuracy, multilingual
   - Cons: Requires more memory
   - Best for: Complex layouts

2. **Tesseract**
   - Pros: Well-established, fast
   - Cons: Requires system installation
   - Best for: Clear, printed text

3. **EasyOCR**
   - Pros: Easy setup, good results
   - Cons: Slower processing
   - Best for: Quick prototyping

### Entity Extraction

Automatic pattern matching for:
- **Prices**: `1.99 €`, `2,50`, etc.
- **Discounts**: `-20%`, `30% off`, etc.
- **Units**: `1 kg`, `500g`, `1L`, etc.
- **Dates**: `01.01.2025`, etc.

### Visualization

- Color-coded confidence levels:
  - 🟢 Green: High confidence (>80%)
  - 🟡 Yellow: Medium confidence (60-80%)
  - 🟠 Orange: Low confidence (<60%)

### Export Options

- **CSV**: For spreadsheet analysis
- **JSON**: For programmatic use
- **Individual or bulk**: Export by entity type or all at once

## Workflow

### Basic Workflow

```
1. Upload Image
   ↓
2. Configure Settings (OCR engine, threshold)
   ↓
3. Click "Extract Information"
   ↓
4. Review Results (tabs 1-2)
   ↓
5. Check Identified Deals (tab 3)
   ↓
6. Export Data
```

### Advanced Workflow

```
1. Upload Multiple Images (one at a time)
   ↓
2. Process Each with Different Settings
   ↓
3. Compare Results (check history)
   ↓
4. Select Best Settings
   ↓
5. Batch Process Remaining Images
   ↓
6. Aggregate and Export All Data
```

## Tips & Tricks

### For Best OCR Results

1. **Image Quality**
   - Use high-resolution images (1000+ pixels wide)
   - Ensure good lighting (no shadows)
   - Avoid blurry or distorted images

2. **Preprocessing**
   - Enable for scanned or photographed brochures
   - Disable for digital PDFs converted to images

3. **Confidence Threshold**
   - Start with 0.5
   - Increase if too many false positives
   - Decrease if missing valid text

4. **OCR Engine Selection**
   - Try all three with a sample image
   - Compare results in the Extracted Data tab
   - Use the best performer for your brochure type

### For Better Deal Detection

1. **Image Cropping**
   - Crop to single deals or product sections
   - Remove header/footer text
   - Focus on relevant content

2. **Layout**
   - Works best with grid layouts
   - Struggles with highly creative designs
   - May need manual verification

3. **Post-Processing**
   - Review identified deals carefully
   - Check the Extracted Data tab for missing entities
   - Export and manually link if needed

### Performance Tips

1. **Image Size**
   - Resize very large images (>4000px) before upload
   - Use JPEG for better upload speed

2. **Batch Processing**
   - Process one image at a time
   - Check history to track progress
   - Export data incrementally

## Troubleshooting

### Common Issues

#### Issue: "OCR processing error"
**Causes**:
- OCR library not installed
- Incompatible image format
- Out of memory

**Solutions**:
1. Install required OCR library:
   ```bash
   pip install paddleocr  # or pytesseract, easyocr
   ```
2. Check image format (PNG, JPG, JPEG only)
3. Reduce image size
4. Try different OCR engine

#### Issue: No text detected
**Causes**:
- Confidence threshold too high
- Poor image quality
- Wrong preprocessing setting

**Solutions**:
1. Lower confidence threshold to 0.3
2. Enable/disable preprocessing
3. Try different OCR engine
4. Enhance image externally (brightness, contrast)

#### Issue: Incorrect entity grouping
**Causes**:
- Complex layout
- Overlapping regions
- Spatial proximity logic

**Solutions**:
1. Crop image to smaller sections
2. Process deals individually
3. Export entities and group manually
4. Adjust proximity thresholds (requires code modification)

#### Issue: App won't start
**Causes**:
- Streamlit not installed
- Port 8501 in use
- Python environment issues

**Solutions**:
1. Install Streamlit: `pip install streamlit`
2. Use different port:
   ```bash
   streamlit run src/app/enhanced_app.py --server.port 8502
   ```
3. Activate virtual environment
4. Check Python version (3.8+ required)

#### Issue: Slow processing
**Causes**:
- Large image size
- CPU-only processing (PaddleOCR)
- System resources

**Solutions**:
1. Resize image before upload
2. Use Tesseract (faster)
3. Disable preprocessing
4. Close other applications

### Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "ModuleNotFoundError: No module named 'paddleocr'" | OCR library missing | `pip install paddleocr` |
| "FileNotFoundError: [Errno 2] No such file or directory: 'tesseract'" | Tesseract not installed | Install Tesseract system-wide |
| "cv2.error: OpenCV(4.x.x) ..." | Image processing error | Check image format/size |
| "MemoryError" | Out of RAM | Reduce image size or use smaller model |

### Getting Help

1. Check the main README.md
2. Review QUICK_START.md
3. Inspect browser console (F12) for JavaScript errors
4. Check terminal output for Python errors
5. Verify all dependencies: `python verify_setup.py`

## Advanced Features

### Custom Configuration

You can modify settings by editing:
- `src/app/enhanced_app.py`: App configuration
- `src/app/utils.py`: Processing parameters
- `src/preprocessing/ocr_pipeline.py`: OCR settings

### API Integration

The app components can be used programmatically:

```python
from app.utils import extract_entities, create_deals_from_entities
from preprocessing.ocr_pipeline import OCRPipeline

# Process image
pipeline = OCRPipeline(ocr_engine='paddleocr')
result = pipeline.process_image('brochure.jpg')

# Extract entities
entities = extract_entities(result['text_boxes'])

# Create deals
deals = create_deals_from_entities(entities)
```

### Batch Processing Script

For processing multiple files, create a script:

```python
import glob
from preprocessing.ocr_pipeline import OCRPipeline

pipeline = OCRPipeline()
for image in glob.glob('data/raw/*.jpg'):
    result = pipeline.process_image(image)
    # Process results...
```

## Best Practices

1. **Start with samples**: Test with 2-3 images before bulk processing
2. **Document settings**: Note which settings work best for your brochure type
3. **Verify results**: Manually check a sample of deals for accuracy
4. **Export regularly**: Don't lose work - export data frequently
5. **Keep originals**: Maintain original images for reprocessing

## Future Enhancements

Planned features for future versions:
- [ ] PDF support
- [ ] Multi-page processing
- [ ] Batch upload
- [ ] Custom entity patterns
- [ ] Model fine-tuning interface
- [ ] Price comparison across brochures
- [ ] Automatic categorization
- [ ] REST API endpoint

---

**Questions or feedback?** Contact the team: Liyang, Zhaokun
