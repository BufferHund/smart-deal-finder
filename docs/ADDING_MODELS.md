# Adding New Models - Developer Guide

This guide shows you how to add new extraction models to SmartDeal in **3 simple steps**.

## Quick Start

### Step 1: Create Your Extractor Class

Create a new file in `src/extractors/` (e.g., `my_extractor.py`):

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model
import numpy as np
from typing import Dict


@register_model("my_model_id")
class MyExtractor(BaseExtractor):
    """Your custom extractor"""

    def __init__(self):
        super().__init__("My Model Name")

    def is_available(self) -> bool:
        """Check if your model can run"""
        try:
            # Check dependencies
            import your_dependency
            return True
        except ImportError:
            return False

    def extract(self, image: np.ndarray, **kwargs) -> Dict:
        """Extract deals from image"""
        try:
            # Your extraction logic here
            deals = []  # Your code extracts deals

            return {
                "deals": deals,
                "total_products": len(deals),
                "extraction_method": self.name,
                "status": "success"
            }
        except Exception as e:
            return {
                "deals": [],
                "total_products": 0,
                "extraction_method": self.name,
                "status": "error",
                "error": str(e)
            }

    def get_info(self) -> Dict:
        """Provide model information"""
        info = super().get_info()
        info.update({
            "type": "your_type",  # "ocr", "ai", "vlm"
            "accuracy": 0.95,     # Estimated accuracy
            "speed": "fast",      # "fast", "medium", "slow"
            "cost": "free"        # "free" or price
        })
        return info
```

### Step 2: Add Model Configuration

Add your model to `src/extractors/models.yaml`:

```yaml
my_model_id:
  name: "My Model Name"
  type: "ai"  # or "ocr", "vlm"
  description: "Brief description of what your model does"
  accuracy: 0.95
  speed: "fast"
  cost: "free"
  requires:
    - your-package
    - another-dependency
```

### Step 3: Import in __init__.py

Add one line to `src/extractors/__init__.py`:

```python
from .my_extractor import MyExtractor
```

**That's it!** Your model is now available throughout the application.

## Detailed Examples

### Example 1: OCR-based Model

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model


@register_model("ocr_easyocr")
class EasyOCRExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("EasyOCR")
        self.reader = None

    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except:
            return False

    def extract(self, image, **kwargs):
        import easyocr

        # Lazy load model
        if self.reader is None:
            self.reader = easyocr.Reader(['en', 'de'])

        # Extract text
        results = self.reader.readtext(image)

        # Process results into deals
        deals = self._process_ocr_results(results)

        return {
            "deals": deals,
            "total_products": len(deals),
            "extraction_method": self.name,
            "status": "success"
        }

    def _process_ocr_results(self, results):
        """Convert OCR output to deals"""
        # Your processing logic
        deals = []
        for (bbox, text, conf) in results:
            # Extract product info
            pass
        return deals
```

### Example 2: Cloud AI Model

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model


@register_model("openai_vision")
class OpenAIExtractor(BaseExtractor):
    def __init__(self):
        super().__init__("OpenAI GPT-4 Vision")

    def is_available(self) -> bool:
        import os
        return "OPENAI_API_KEY" in os.environ

    def extract(self, image, **kwargs):
        import openai
        import base64
        from io import BytesIO
        from PIL import Image

        # Convert numpy to base64
        pil_image = Image.fromarray(image)
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": self._get_prompt()},
                    {"type": "image_url", "image_url": f"data:image/png;base64,{img_base64}"}
                ]
            }]
        )

        # Parse response
        deals = self._parse_response(response)

        return {
            "deals": deals,
            "total_products": len(deals),
            "extraction_method": self.name,
            "status": "success"
        }

    def _get_prompt(self):
        return "Extract all product deals from this brochure..."

    def _parse_response(self, response):
        # Parse JSON from response
        import json
        text = response.choices[0].message.content
        return json.loads(text)
```

### Example 3: Local VLM Model

```python
from extractors.base import BaseExtractor
from extractors.model_registry import register_model


@register_model("huggingface_vlm")
class HuggingFaceVLM(BaseExtractor):
    def __init__(self):
        super().__init__("HuggingFace VLM")
        self.model = None
        self.processor = None

    def is_available(self) -> bool:
        try:
            import transformers
            return True
        except:
            return False

    def extract(self, image, **kwargs):
        from transformers import AutoProcessor, AutoModelForVision2Seq
        from PIL import Image

        # Lazy load model
        if self.model is None:
            self.processor = AutoProcessor.from_pretrained("your-model")
            self.model = AutoModelForVision2Seq.from_pretrained("your-model")

        # Prepare inputs
        pil_image = Image.fromarray(image)
        inputs = self.processor(
            images=pil_image,
            text=self._get_prompt(),
            return_tensors="pt"
        )

        # Generate
        outputs = self.model.generate(**inputs)
        text = self.processor.decode(outputs[0])

        # Parse output
        deals = self._parse_output(text)

        return {
            "deals": deals,
            "total_products": len(deals),
            "extraction_method": self.name,
            "status": "success"
        }
```

## Best Practices

### 1. Lazy Loading

Load heavy models only when needed:

```python
def __init__(self):
    super().__init__("My Model")
    self.model = None  # Don't load yet

def extract(self, image, **kwargs):
    if self.model is None:
        self.model = load_heavy_model()  # Load on first use
    # Use model
```

### 2. Error Handling

Always wrap extraction in try-except:

```python
def extract(self, image, **kwargs):
    try:
        # Extraction logic
        return {"status": "success", ...}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "deals": [],
            "total_products": 0
        }
```

### 3. Configuration

Store model-specific config in class attributes:

```python
class MyExtractor(BaseExtractor):
    MODEL_NAME = "model-v2"
    MAX_TOKENS = 2048
    TEMPERATURE = 0.1

    def extract(self, image, **kwargs):
        # Use self.MODEL_NAME, etc.
```

### 4. Caching

Cache expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def _preprocess_image(self, image_hash):
    # Expensive preprocessing
    return processed_image
```

### 5. Testing

Add tests for your extractor:

```python
# tests/test_my_extractor.py
def test_my_extractor():
    extractor = MyExtractor()
    assert extractor.is_available()

    result = extractor.extract(test_image)
    assert result["status"] == "success"
    assert len(result["deals"]) > 0
```

## Common Patterns

### Pattern 1: Model with API Key

```python
import os

def is_available(self) -> bool:
    return "MY_API_KEY" in os.environ

def extract(self, image, **kwargs):
    api_key = os.getenv("MY_API_KEY")
    # Use API key
```

### Pattern 2: Model with Multiple Variants

```python
@register_model("my_model_small")
class MyModelSmall(BaseExtractor):
    MODEL_SIZE = "small"

@register_model("my_model_large")
class MyModelLarge(BaseExtractor):
    MODEL_SIZE = "large"
```

### Pattern 3: Model with Progress Callback

```python
def extract(self, image, progress_callback=None, **kwargs):
    if progress_callback:
        progress_callback("Loading model...")

    model = load_model()

    if progress_callback:
        progress_callback("Extracting...")

    result = model.predict(image)

    if progress_callback:
        progress_callback("Done!")

    return result
```

## Troubleshooting

### Model Not Showing Up?

1. Check `is_available()` returns `True`
2. Verify decorator `@register_model()` is present
3. Ensure import in `__init__.py`
4. Check for syntax errors in your file

### Import Errors?

Add parent directory to path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Model Running Slowly?

1. Use lazy loading
2. Cache loaded models
3. Batch process multiple images
4. Use GPU if available

## Next Steps

1. **Test your extractor** with sample images
2. **Add to models.yaml** with accurate metadata
3. **Update documentation** if needed
4. **Submit PR** or integrate into your branch

## Getting Help

- Check existing extractors in `src/extractors/`
- Read [ARCHITECTURE.md](./ARCHITECTURE.md)
- Contact team: Liyang, Zhaokun

---

**Happy Model Building!** 🚀
