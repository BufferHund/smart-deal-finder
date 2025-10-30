# SmartDeal: Supermarket Brochure Information Extraction

## Problem Description
Supermarket brochures contain valuable information about weekly discounts, product offers, and price changes. However, these brochures are usually published as unstructured images or PDFs, which makes it difficult for customers to extract and analyze deals.

## Project Aims
Build an intelligent system that automatically detects and extracts structured deal information—such as product names, prices, and discounts—from these visually complex brochures. Structured access to this information helps users find cheaper or local alternatives.

## Planned Application
A lightweight web app where users can:
- Upload a brochure page (PDF or image)
- View the original image with detected deal regions highlighted
- Receive structured table or JSON output listing extracted items
- Get purchasing recommendations considering multiple factors

## Methodology
1. **OCR & Layout Analysis**: Text detection and recognition via Tesseract or PaddleOCR; region grouping by visual and spatial heuristics
2. **Information Extraction**: Entity recognition using layout-aware transformers (LayoutLMv3) or OCR-free models (Donut)
3. **Fine-tuning**: PEFT (Parameter-Efficient Fine-Tuning) on collected data

## Main Challenges
- **Data format variation**: PDF, pictures, scanned copies
- **Layout variability**: Different retailer designs
- **OCR noise**: Distorted fonts and price symbols
- **Entity alignment**: Linking visual blocks with semantic fields
- **Limited labeled data**: Small annotated dataset

## Project Timeline (8 Weeks)

### Week 1: Project Setup & Data Collection Planning
- Define project scope and objectives
- Collect supermarket brochure samples
- Design data storage structure

### Week 2: Data Collection & Initial Preprocessing
- Download and clean brochure data
- Standardize formats and resolutions
- Run initial OCR extraction

### Week 3: Data Annotation & Standardization
- Manually annotate sample pages
- Define JSON schema for structured data
- Evaluate OCR accuracy

### Week 4: Model Selection & Environment Setup
- Research LayoutLMv3, Donut, PaddleOCR
- Configure training environment
- Design model pipeline

### Week 5: Model Fine-tuning
- Apply PEFT on labeled data
- Tune hyperparameters
- Perform data augmentation

### Week 6: Evaluation & Refinement
- Evaluate extraction accuracy
- Conduct error analysis
- Iterate improvements

### Week 7: Application Prototyping
- Develop web UI
- Implement visualization features
- Create structured output display

### Week 8: Integration, Testing & Presentation
- Integrate model with front-end
- Test across various formats
- Prepare final report

## Target Supermarkets

| Supermarket | Website | PDF Available |
|------------|---------|---------------|
| Aldi Süd | https://prospekt.aldi-sued.de/ | ✅ |
| Aldi Nord | https://www.aldi-nord.de/prospekte/ | ✅ |
| Lidl | https://www.lidl.de/l/prospekte/ | ❌ (web scraping) |
| Rewe | https://www.rewe.de/ | ✅ |
| Edeka | https://www.edeka.de/ | ✅ |
| Penny | https://www.penny.de/angebote | TBD |
| Netto | https://www.netto-online.de/ | TBD |
| Kaufland | https://www.kaufland.de/ | TBD |

## Project Structure
```
smartdeal/
├── data/
│   ├── raw/              # Raw brochure PDFs and images
│   ├── processed/        # Preprocessed and standardized data
│   └── annotations/      # Manually annotated data
├── src/
│   ├── data_collection/  # Web scraping and download scripts
│   ├── preprocessing/    # OCR and data standardization
│   ├── models/          # Model training and inference
│   ├── evaluation/      # Evaluation metrics and analysis
│   └── app/             # Web application
├── notebooks/           # Jupyter notebooks for exploration
├── tests/              # Unit tests
├── config/             # Configuration files
└── requirements.txt    # Python dependencies
```

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd smartdeal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Data Collection
```bash
python src/data_collection/scraper.py --supermarket aldi
```

### Preprocessing
```bash
python src/preprocessing/ocr_pipeline.py --input data/raw --output data/processed
```

### Model Training
```bash
python src/models/train.py --config config/train_config.yaml
```

### Web Application
```bash
streamlit run src/app/app.py
```

## Technologies
- **OCR**: Tesseract, PaddleOCR, EasyOCR
- **ML Models**: LayoutLMv3, Donut, TrOCR
- **Fine-tuning**: PEFT, LoRA
- **Web Framework**: Streamlit or Flask
- **Computer Vision**: OpenCV, PIL
- **Data Processing**: pandas, numpy

## Team
- Liyang
- Zhaokun

## License
MIT License
