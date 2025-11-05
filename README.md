# SmartDeal: Brochure Information Extraction System

An extensible framework for extracting product deals from supermarket brochures using multiple AI models.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

SmartDeal automatically extracts structured deal information (products, prices, discounts) from visually complex supermarket brochures. The system features a plugin-based architecture that makes it easy to add and switch between different extraction models.

### Key Features

- Multiple Extraction Models: OCR, Gemini AI, Ollama VLM
- Plugin Architecture: Add new models in 3 simple steps
- Model Registry: Automatic model discovery and management
- PDF Support: Process multi-page brochures
- Well-Documented: Comprehensive guides for developers

## Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd smartdeal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Application

```bash
# Launch application
streamlit run src/app/enhanced_app.py

# Or use the launcher script
./run_app.sh
```

Visit http://localhost:8501

## Available Models

### OCR-Based
- **Tesseract OCR**: Fast, free, ~90% accuracy
- **PaddleOCR**: Advanced, ~92% accuracy

### AI-Based
- **Gemini 2.0 Flash**: Best quality, ~98% accuracy
- **Ollama VLM**: Local AI, ~90-95% accuracy, free
  - Qwen2.5-VL (7B) - Most powerful
  - LLaVA (7B) - Reliable
  - Llama 3.2 Vision (11B) - Latest
  - LLaVA-Phi3 (3.8B) - Fastest

## Architecture

```
smartdeal/
├── src/
│   ├── extractors/         # Model plugins (extensible)
│   │   ├── base.py         # Abstract interface
│   │   ├── model_registry.py
│   │   ├── models.yaml
│   │   ├── ocr_extractor.py
│   │   ├── gemini_extractor.py
│   │   └── ollama_extractor.py
│   ├── preprocessing/      # PDF/Image processing
│   ├── app/               # Frontend applications
│   └── config/            # Configuration
├── docs/                  # Documentation
├── tests/                 # Unit tests
└── data/samples/          # Sample brochures
```

### Plugin Architecture

Adding a new model:

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model

@register_model("my_model")
class MyExtractor(BaseExtractor):
    def is_available(self) -> bool:
        return True

    def extract(self, image, **kwargs):
        return {"deals": [...], "status": "success"}
```

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design principles
- **[ADDING_MODELS.md](docs/ADDING_MODELS.md)** - Step-by-step guide for adding models

## Configuration

### Model Configuration (`src/extractors/models.yaml`)

```yaml
my_model:
  name: "My Custom Model"
  type: "ai"
  description: "Description here"
  accuracy: 0.95
  speed: "fast"
  cost: "free"
```

### Application Settings (`src/config/settings.py`)

```python
class Config:
    DEFAULT_OCR_ENGINE = "tesseract"
    DEFAULT_VLM_MODEL = "qwen2.5vl:7b"
    MAX_FILE_SIZE_MB = 50
```

## Usage Examples

### Python API

```python
from extractors.model_registry import registry

# List available models
models = registry.list_available()

# Use a specific model
extractor = registry.get("ocr_tesseract")
result = extractor.extract(image)
```

### Command Line

```bash
# Extract from a brochure
python -m src.extractors.cli extract --model ocr_tesseract --input brochure.pdf

# List available models
python -m src.extractors.cli list-models
```

## Testing

```bash
# Run all tests
pytest tests/

# With coverage
pytest --cov=src tests/
```

## Model Comparison

| Model | Accuracy | Speed | Cost | Best For |
|-------|----------|-------|------|----------|
| Tesseract OCR | ~90% | 3-4s | Free | High volume |
| PaddleOCR | ~92% | 5-6s | Free | Asian languages |
| Gemini Flash | ~98% | 10s | $0.005 | Best quality |
| Qwen2.5-VL | ~95% | 15s | Free | Local/Privacy |
| LLaVA | ~90% | 15s | Free | Balanced |

## Development

### Adding a New Model

See [ADDING_MODELS.md](docs/ADDING_MODELS.md) for detailed instructions.

Steps:
1. Create extractor class with `@register_model()` decorator
2. Add configuration to `models.yaml`
3. Import in `__init__.py`

### Project Structure

- **`src/extractors/`**: Core extraction models
- **`src/preprocessing/`**: PDF and image processing
- **`src/app/`**: Frontend applications
- **`tests/`**: Unit and integration tests
- **`docs/`**: Documentation

## Roadmap

- REST API with FastAPI
- Model ensemble
- Fine-tuning support
- Performance monitoring
- Docker deployment
- Batch processing API

## Contributing

1. Fork the repository
2. Create your feature branch
3. Follow the [ADDING_MODELS.md](docs/ADDING_MODELS.md) guide
4. Add tests for your changes
5. Submit a Pull Request

## Target Supermarkets

- Aldi Süd/Nord
- REWE
- Edeka
- Lidl
- Penny
- Netto
- Kaufland

## Technologies

**Core**: Python 3.12+, Streamlit, pandas, numpy
**OCR**: Tesseract, PaddleOCR
**AI**: Google Gemini API, Ollama (LLaVA, Qwen, Llama)
**Image Processing**: OpenCV, Pillow

## License

This project is licensed under the MIT License.
