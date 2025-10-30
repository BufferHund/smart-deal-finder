# SmartDeal Web Application

Professional web interface for supermarket brochure information extraction.

## Features

### Core Functionality
- **Multi-Engine OCR**: Support for PaddleOCR, Tesseract, and EasyOCR
- **Smart Entity Extraction**: Automatic detection of products, prices, discounts, units
- **Deal Recognition**: Intelligent grouping of related entities
- **Visual Analysis**: Bounding box visualization with confidence scores
- **Data Export**: CSV and JSON export options
- **Session Management**: Track processing history

### User Interface
- **Responsive Design**: Works on desktop and tablet
- **Four Main Tabs**:
  1. Upload & Process: Image upload and OCR processing
  2. Extracted Data: View and export all detected entities
  3. Deals Analysis: Structured deal information
  4. History: Processing history and statistics

### Advanced Features
- Real-time processing feedback
- Adjustable confidence thresholds
- Image preprocessing options
- Color-coded confidence visualization
- Session state persistence
- Batch processing capability (via history)

## Quick Start

### Launch the Application

**Using the launch script (recommended):**
```bash
./run_app.sh
```

**Using Streamlit directly:**
```bash
streamlit run src/app/enhanced_app.py
```

The app will open at `http://localhost:8501`

### Basic Usage

1. **Upload Image**
   - Click "Browse files" or drag & drop
   - Supports PNG, JPG, JPEG formats

2. **Configure Settings**
   - Select OCR engine (sidebar)
   - Adjust confidence threshold
   - Enable/disable preprocessing

3. **Process**
   - Click "Extract Information"
   - Wait for processing to complete

4. **Review Results**
   - View bounding boxes on image
   - Check extracted data in tabs
   - Examine identified deals

5. **Export Data**
   - Download as CSV or JSON
   - Export individual entity types or complete dataset

## Architecture

### Application Structure

```
src/app/
├── app.py              # Original simple version
├── enhanced_app.py     # Full-featured version
├── utils.py           # Utility functions
└── README.md          # This file
```

### Key Components

#### enhanced_app.py
Main application with:
- Streamlit UI configuration
- Session state management
- OCR integration
- Entity extraction pipeline
- Export functionality

#### utils.py
Helper functions:
- `draw_bounding_boxes()`: Visualize OCR results
- `extract_entities()`: Pattern-based entity extraction
- `entities_to_dataframe()`: Convert to pandas DataFrame
- `create_deals_from_entities()`: Group entities into deals
- `export_to_json()`: JSON export
- `export_to_csv()`: CSV export
- `calculate_bbox_distance()`: Spatial proximity calculation

### Data Flow

```
Image Upload
    ↓
OCR Processing (preprocessing.ocr_pipeline)
    ↓
Text Boxes with Bounding Boxes
    ↓
Entity Extraction (utils.extract_entities)
    ↓
Categorized Entities
    ↓
Deal Creation (utils.create_deals_from_entities)
    ↓
Structured Deals
    ↓
Visualization & Export
```

## Configuration

### OCR Engines

Configure in sidebar:
- **PaddleOCR**: Best accuracy, multilingual support
- **Tesseract**: Fast, requires system installation
- **EasyOCR**: Easy setup, good results

### Processing Parameters

Adjustable settings:
- **Confidence Threshold**: 0.0-1.0 (default: 0.5)
- **Preprocessing**: Enable/disable (default: enabled)
- **Display Options**: Bounding boxes, text labels, confidence scores

### Entity Detection Patterns

Defined in `utils.py`:
```python
price_pattern = r'(\d+[,.]?\d{0,2})\s*€?'
discount_pattern = r'(-?\d+)\s*%'
unit_pattern = r'(\d+\.?\d*)\s*(kg|g|l|ml|stk|stück|pack|dose)'
date_pattern = r'(\d{1,2}[./]\d{1,2}[./]\d{2,4})'
```

Modify these for custom detection needs.

### Deal Grouping Parameters

Proximity threshold in `create_deals_from_entities()`:
```python
proximity_threshold = 200  # pixels
```

Adjust based on your brochure layouts.

## Dependencies

### Required Packages
```
streamlit>=1.28.0
opencv-python>=4.8.0
pillow>=10.0.0
numpy>=1.24.0
pandas>=2.0.0
```

### OCR Libraries (at least one required)
```
paddleocr>=2.7.0
pytesseract>=0.3.10
easyocr>=1.7.0
```

### System Requirements
- Python 3.8+
- 4GB+ RAM
- (Optional) GPU for PaddleOCR acceleration
- (Optional) Tesseract system installation

## API Reference

### Utility Functions

#### draw_bounding_boxes
```python
def draw_bounding_boxes(
    image: np.ndarray,
    text_boxes: List[Dict],
    confidence_threshold: float = 0.5,
    show_text: bool = True,
    show_confidence: bool = False
) -> np.ndarray
```

Draws bounding boxes on image with optional labels.

**Parameters:**
- `image`: Input image as numpy array
- `text_boxes`: List of text boxes from OCR
- `confidence_threshold`: Minimum confidence to display
- `show_text`: Whether to show extracted text
- `show_confidence`: Whether to show confidence scores

**Returns:** Image with bounding boxes drawn

#### extract_entities
```python
def extract_entities(text_boxes: List[Dict]) -> Dict[str, List[Dict]]
```

Extract structured entities from OCR results.

**Parameters:**
- `text_boxes`: List of text boxes with text and bbox

**Returns:** Dictionary with entity categories:
- `prices`: Monetary values
- `discounts`: Percentage discounts
- `products`: Product names
- `units`: Quantities and units
- `dates`: Date information
- `other`: Uncategorized text

#### create_deals_from_entities
```python
def create_deals_from_entities(entities: Dict[str, List[Dict]]) -> List[Dict]
```

Create structured deals by grouping nearby entities.

**Parameters:**
- `entities`: Dictionary of extracted entities

**Returns:** List of deal dictionaries with:
- `product_name`: Product name
- `price`: Price value
- `discount`: Discount percentage
- `unit`: Unit information
- Bounding boxes for each component

## Customization

### Adding New Entity Types

1. Define pattern in `utils.py`:
```python
new_pattern = r'your_regex_pattern'
```

2. Add to `extract_entities()`:
```python
new_match = re.search(new_pattern, text, re.IGNORECASE)
if new_match:
    entities['new_type'].append({...})
```

3. Update UI in `enhanced_app.py` to display new type

### Custom Visualization

Modify `draw_bounding_boxes()` to change:
- Colors: Update RGB tuples
- Line width: Adjust `width` parameter
- Font: Change font path or size
- Background: Modify rectangle fill

### Export Formats

Add new export format:
```python
def export_to_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_excel(output, index=False)
    return output.getvalue()
```

Then add download button in app.

## Troubleshooting

### Common Issues

**OCR not working:**
- Check if OCR library is installed
- Verify image format (PNG, JPG, JPEG)
- Try different OCR engine

**Poor extraction results:**
- Adjust confidence threshold
- Enable/disable preprocessing
- Use higher resolution images

**Deals not grouping correctly:**
- Reduce proximity threshold in code
- Process smaller image sections
- Verify entity detection first

**App crashes:**
- Reduce image size
- Check memory usage
- Restart Streamlit server

### Debug Mode

Enable Streamlit debug mode:
```bash
streamlit run src/app/enhanced_app.py --logger.level=debug
```

View session state:
```python
st.write(st.session_state)  # Add to app for debugging
```

## Performance

### Optimization Tips

1. **Image Size**: Keep under 2000px width
2. **OCR Engine**: Tesseract is fastest
3. **Preprocessing**: Disable for clean images
4. **Batch Processing**: Process offline, load results

### Benchmarks

Approximate processing times (1500x1000px image):
- PaddleOCR: 3-5 seconds (CPU), 1-2 seconds (GPU)
- Tesseract: 1-2 seconds
- EasyOCR: 5-8 seconds

## Development

### Running in Development Mode

```bash
streamlit run src/app/enhanced_app.py --server.runOnSave true
```

### Adding Features

1. Create feature in separate function
2. Add UI elements in appropriate tab
3. Update session state if needed
4. Test with sample data
5. Add to documentation

### Testing

Manual testing checklist:
- [ ] Upload various image formats
- [ ] Test all OCR engines
- [ ] Verify entity extraction
- [ ] Check deal grouping
- [ ] Test export functions
- [ ] Verify session persistence
- [ ] Test error handling

## Deployment

### Local Deployment

Already configured for local use. Just run:
```bash
./run_app.sh
```

### Remote Deployment

#### Streamlit Cloud
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Configure secrets if needed
4. Deploy

#### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "src/app/enhanced_app.py"]
```

Build and run:
```bash
docker build -t smartdeal .
docker run -p 8501:8501 smartdeal
```

## Version History

### v1.0 (Current)
- Initial release
- Three OCR engines
- Entity extraction
- Deal recognition
- CSV/JSON export
- Processing history

### Planned Features
- [ ] PDF support
- [ ] Multi-page processing
- [ ] Batch upload
- [ ] Custom training interface
- [ ] Price comparison dashboard
- [ ] REST API

## Contributing

To contribute:
1. Create feature branch
2. Implement feature
3. Test thoroughly
4. Update documentation
5. Submit for review

## License

MIT License - Part of the SmartDeal project

## Support

For issues or questions:
- Check docs/WEB_APP_GUIDE.md
- Review main README.md
- Contact team: Liyang, Zhaokun

---

**Built with Streamlit** | **Team: Liyang & Zhaokun** | **Version 1.0**
