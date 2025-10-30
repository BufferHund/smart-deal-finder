# Quick Start Guide

This guide will help you get started with the SmartDeal project.

## Prerequisites

- Python 3.8 or higher
- Git
- pip (Python package manager)
- (Optional) Tesseract OCR for text extraction

## Installation

### 1. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install required packages
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install System Dependencies

#### Tesseract OCR (Optional but recommended)

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # For German language support
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-deu  # German language
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

## Usage

### Week 1-2: Data Collection

#### 1. Collect Brochure Data

```bash
# List available scrapers
python src/data_collection/scraper.py --list

# Download Aldi Süd brochures
python src/data_collection/scraper.py --supermarket aldi_sued

# Download Aldi Nord brochures
python src/data_collection/scraper.py --supermarket aldi_nord

# Limit downloads (for testing)
python src/data_collection/scraper.py --supermarket aldi_sued --max 5
```

#### 2. Verify Downloaded Data

```bash
# Check downloaded files
ls -R data/raw/

# Count files
find data/raw -type f | wc -l
```

### Week 2-3: OCR Processing

#### 1. Run OCR Pipeline

```bash
# Process single image
python src/preprocessing/ocr_pipeline.py \
    --input data/raw/aldi_sued/image.jpg \
    --output data/processed \
    --engine paddleocr

# Process entire directory
python src/preprocessing/ocr_pipeline.py \
    --input data/raw/aldi_sued \
    --output data/processed \
    --engine paddleocr
```

#### 2. Compare OCR Engines

```bash
# Try different engines
python src/preprocessing/ocr_pipeline.py --input data/raw/sample.jpg --output results/paddleocr --engine paddleocr
python src/preprocessing/ocr_pipeline.py --input data/raw/sample.jpg --output results/tesseract --engine tesseract
python src/preprocessing/ocr_pipeline.py --input data/raw/sample.jpg --output results/easyocr --engine easyocr
```

### Week 3: Data Exploration

```bash
# Start Jupyter notebook
jupyter notebook notebooks/01_data_exploration.ipynb
```

### Week 7: Web Application

```bash
# Run Streamlit app
streamlit run src/app/app.py

# The app will open in your browser at http://localhost:8501
```

## Project Structure

```
smartdeal/
├── data/
│   ├── raw/              # Downloaded brochures
│   ├── processed/        # OCR results (JSON)
│   └── annotations/      # Manual annotations
├── src/
│   ├── data_collection/  # Scraping scripts
│   │   ├── scraper.py           # Main script
│   │   ├── base_scraper.py      # Base class
│   │   ├── aldi_scraper.py      # Aldi-specific
│   │   └── scraper_factory.py   # Factory pattern
│   ├── preprocessing/    # OCR pipeline
│   │   └── ocr_pipeline.py      # OCR processing
│   ├── models/          # Model training (Week 4-5)
│   ├── evaluation/      # Evaluation scripts (Week 6)
│   └── app/             # Web application (Week 7-8)
│       └── app.py               # Streamlit app
├── notebooks/           # Jupyter notebooks
│   └── 01_data_exploration.ipynb
├── config/              # Configuration files
│   ├── data_sources.yaml        # Supermarket URLs
│   └── annotation_schema.json   # Annotation format
└── requirements.txt     # Python dependencies
```

## Common Issues & Solutions

### Issue: PaddleOCR Installation Fails

**Solution:**
```bash
# Install with specific version
pip install paddlepaddle==2.5.0
pip install paddleocr==2.7.0
```

### Issue: Tesseract Not Found

**Solution:**
Make sure Tesseract is installed and in your PATH:
```bash
# Test Tesseract
tesseract --version

# If not found, install it (see Installation section above)
```

### Issue: Memory Error During OCR

**Solution:**
Process images in smaller batches:
```bash
# Process with smaller batch
python src/preprocessing/ocr_pipeline.py --input data/raw --output data/processed --batch-size 10
```

## Development Workflow

### Week 1: Setup & Initial Data Collection
1. ✅ Set up project structure
2. ✅ Install dependencies
3. Run scrapers to collect 10-20 sample brochures
4. Verify data quality

### Week 2: OCR Testing
1. Test different OCR engines
2. Compare accuracy and speed
3. Select best approach
4. Process collected brochures

### Week 3: Annotation
1. Set up annotation tool
2. Manually annotate 10-15 pages
3. Document annotation guidelines
4. Create training/validation split

### Week 4: Model Selection
1. Research LayoutLMv3 and Donut
2. Set up training environment
3. Prepare data loaders
4. Baseline model testing

### Week 5: Fine-tuning
1. Train model on annotated data
2. Hyperparameter tuning
3. Data augmentation
4. Save best model

### Week 6: Evaluation
1. Test on validation set
2. Error analysis
3. Improve post-processing
4. Document results

### Week 7: Web App Development
1. Integrate model with Streamlit
2. Add visualization features
3. Implement file upload
4. User testing

### Week 8: Final Integration
1. Bug fixes
2. Documentation
3. Prepare presentation
4. Demo video

## Testing

```bash
# Run tests (when available)
pytest tests/

# Run specific test
pytest tests/test_scraper.py

# Run with coverage
pytest --cov=src tests/
```

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push and create pull request

## Getting Help

- Check the main README.md for detailed documentation
- Review example notebooks in `notebooks/`
- Check configuration files in `config/`
- Review code documentation in source files

## Next Steps

1. **Now:** Run the data collection script
   ```bash
   python src/data_collection/scraper.py --supermarket aldi_sued --max 10
   ```

2. **After data collection:** Run OCR pipeline
   ```bash
   python src/preprocessing/ocr_pipeline.py --input data/raw --output data/processed
   ```

3. **Explore results:** Open Jupyter notebook
   ```bash
   jupyter notebook notebooks/01_data_exploration.ipynb
   ```

4. **Try the web app:** Launch Streamlit
   ```bash
   streamlit run src/app/app.py
   ```

Good luck with your project!
