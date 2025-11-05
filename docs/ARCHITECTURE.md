# SmartDeal Architecture

## Overview

SmartDeal is built with **extensibility** as the core principle. The architecture allows easy addition of new extraction models without modifying existing code.

## Core Components (Simplified)

```
smartdeal/
├── src/
│   ├── extractors/          ← Core: Model plugins (extensible)
│   ├── preprocessing/        ← PDF/Image processing
│   ├── app/                 ← Frontend applications
│   └── config/              ← Configuration (settings only)
├── data/samples/            ← Sample brochures for testing
├── tests/                   ← Unit tests (to be implemented)
└── docs/                    ← English documentation
```

**Simplified structure**: Removed data collection, evaluation, model training modules, and old documentation to focus on the core extraction framework.

## Architecture Layers

### 1. Extractor Layer (`src/extractors/`)

The heart of the system. All extraction models are plugins that implement a common interface.

```
extractors/
├── base.py              # Abstract interface
├── model_registry.py    # Centralized model management
├── models.yaml          # Model configurations
├── ocr_extractor.py     # OCR-based models
├── gemini_extractor.py  # Gemini AI model
└── ollama_extractor.py  # Ollama VLM models
```

**Key Files:**

- **`base.py`**: Defines `BaseExtractor` interface that all models must implement
- **`model_registry.py`**: Automatic model discovery and registration
- **`models.yaml`**: Declarative model configurations

**Design Pattern: Plugin Architecture**

New models are automatically discovered when they:
1. Inherit from `BaseExtractor`
2. Use the `@register_model()` decorator
3. Implement required methods

### 2. Preprocessing Layer (`src/preprocessing/`)

Handles document processing before extraction.

```
preprocessing/
├── pdf_processor.py     # PDF to image conversion
└── ocr_pipeline.py      # OCR text extraction
```

**Responsibilities:**
- Convert PDF to images
- Run OCR (Tesseract, PaddleOCR)
- Image preprocessing (resize, denoise, etc.)

### 3. Application Layer (`src/app/`)

User interfaces built on top of the extractor layer.

```
app/
├── enhanced_app.py      # Full-featured Streamlit app
└── demo_app.py          # Simplified demo app
```

**Frontend is decoupled from backend** - switching models requires no frontend changes.

### 4. Configuration Layer (`src/config/`)

Centralized configuration management.

```
config/
└── settings.py          # Application settings
```

## Data Flow

```
┌─────────────┐
│   Upload    │
│ PDF/Image   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Preprocessing  │
│  - PDF to Image │
│  - OCR Pipeline │
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Model Registry   │
│ - Select Model   │
│ - Check Available│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Extractor      │
│ - OCR            │
│ - Gemini AI      │
│ - Ollama VLM     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│    Results       │
│ - JSON           │
│ - CSV            │
│ - Display        │
└──────────────────┘
```

## Model Registry Pattern

The `ModelRegistry` class provides centralized model management:

```python
from extractors.model_registry import registry

# List available models
models = registry.list_available()

# Get a specific model
extractor = registry.get("ocr_tesseract")

# Extract deals
result = extractor.extract(image)
```

### Benefits:

1. **Decoupling**: Frontend doesn't need to know about model implementations
2. **Discoverability**: Models are automatically found
3. **Flexibility**: Easy to add/remove models
4. **Testability**: Each model can be tested independently

## Adding New Models

See [ADDING_MODELS.md](./ADDING_MODELS.md) for detailed guide.

**Quick Example:**

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model

@register_model("my_model")
class MyExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("My Model")

    def is_available(self) -> bool:
        return True  # Check dependencies

    def extract(self, image, **kwargs):
        # Your extraction logic
        return {"deals": [...], "status": "success"}
```

That's it! The model is now available to all applications.

## Configuration Management

Models are configured in `models.yaml`:

```yaml
my_model:
  name: "My Custom Model"
  type: "ai"
  description: "Description here"
  accuracy: 0.95
  speed: "fast"
  cost: "free"
  requires:
    - some-package
```

## Design Principles

1. **Plugin Architecture**: Models are independent plugins
2. **Interface Segregation**: Simple, focused interfaces
3. **Dependency Inversion**: High-level modules don't depend on low-level details
4. **Open/Closed**: Open for extension, closed for modification
5. **Single Responsibility**: Each module has one reason to change

## Technology Stack

- **Backend**: Python 3.12+
- **Frontend**: Streamlit
- **OCR**: Tesseract, PaddleOCR
- **AI**: Google Gemini, Ollama (LLaVA, Qwen, Llama)
- **Image Processing**: OpenCV, Pillow
- **Data**: pandas, numpy

## Performance Considerations

### Model Selection

Different models have different trade-offs:

| Model | Speed | Accuracy | Cost | Use Case |
|-------|-------|----------|------|----------|
| OCR | Fast (3-4s) | 90% | Free | High volume |
| Gemini | Fast (10s) | 98% | $0.005 | Best quality |
| Ollama | Medium (15s) | 90-95% | Free | Local/Privacy |

### Optimization Strategies

1. **Caching**: Cache model loading and results
2. **Batching**: Process multiple pages together
3. **Async**: Use async processing for I/O operations
4. **Model Selection**: Choose appropriate model for task

## Security Considerations

1. **API Keys**: Never commit API keys, use environment variables
2. **File Upload**: Validate file types and sizes
3. **Model Isolation**: Each model runs in isolated environment
4. **Data Privacy**: Local models keep data on-premises

## Testing Strategy

```
tests/
├── test_extractors.py       # Unit tests for each extractor
├── test_preprocessing.py    # Preprocessing tests
├── test_model_registry.py   # Registry tests
└── test_integration.py      # End-to-end tests
```

## Future Enhancements

1. **REST API**: Add FastAPI backend
2. **Model Ensemble**: Combine multiple models
3. **Fine-tuning**: Train custom models
4. **Monitoring**: Add performance metrics
5. **Deployment**: Docker containerization

---

**Last Updated**: 2025-11-05
**Version**: 2.0
**Team**: Liyang, Zhaokun
