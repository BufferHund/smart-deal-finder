"""Ollama VLM Extractor - Simple and reliable VLM extraction using Ollama"""

import json
import base64
from io import BytesIO
from typing import Dict, List, Optional
import numpy as np
from PIL import Image


def check_ollama_available() -> bool:
    """Check if Ollama service is running"""
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def get_available_ollama_models() -> List[Dict]:
    """
    Get list of available Ollama VLM models

    Returns:
        List of model dictionaries with info
    """
    models = [
        {
            "name": "Qwen2.5-VL 7B",
            "model_id": "qwen2.5vl:7b",
            "description": "Most powerful vision model (~6.0GB)",
            "size": "~6.0 GB",
            "speed": "Fast",
            "accuracy": "Excellent",
            "downloaded": False
        },
        {
            "name": "Llama 3.2 Vision 11B",
            "model_id": "llama3.2-vision:11b",
            "description": "Meta's latest vision model (~7.8GB)",
            "size": "~7.8 GB",
            "speed": "Fast",
            "accuracy": "Excellent",
            "downloaded": False
        },
        {
            "name": "LLaVA 7B",
            "model_id": "llava:7b",
            "description": "Proven reliable model (~4.1GB)",
            "size": "~4.1 GB",
            "speed": "Fast",
            "accuracy": "Very Good",
            "downloaded": False
        },
        {
            "name": "LLaVA-Llama3 8B",
            "model_id": "llava-llama3",
            "description": "LLaVA with Llama3 base (~5.5GB)",
            "size": "~5.5 GB",
            "speed": "Fast",
            "accuracy": "Very Good",
            "downloaded": False
        },
        {
            "name": "LLaVA-Phi3 3.8B",
            "model_id": "llava-phi3",
            "description": "Smallest and fastest (~2.3GB)",
            "size": "~2.3 GB",
            "speed": "Very Fast",
            "accuracy": "Good",
            "downloaded": False
        },
        {
            "name": "Llama 3.2 Vision 90B",
            "model_id": "llama3.2-vision:90b",
            "description": "Highest accuracy, needs powerful GPU (~55GB)",
            "size": "~55 GB",
            "speed": "Slow",
            "accuracy": "Excellent",
            "downloaded": False
        }
    ]

    # Check which models are downloaded
    try:
        import ollama
        downloaded_models = ollama.list()
        downloaded_names = {m['name'] for m in downloaded_models.get('models', [])}

        for model in models:
            # Check if model is downloaded (with or without tag)
            model_base = model['model_id'].split(':')[0]
            model['downloaded'] = any(
                model['model_id'] in name or model_base in name
                for name in downloaded_names
            )
    except Exception:
        pass

    return models


def check_model_downloaded(model_id: str) -> bool:
    """
    Check if a specific Ollama model is downloaded

    Args:
        model_id: Ollama model identifier (e.g., "llava:7b-v1.6")

    Returns:
        True if model is downloaded
    """
    try:
        import ollama
        downloaded_models = ollama.list()
        downloaded_names = {m['name'] for m in downloaded_models.get('models', [])}

        model_base = model_id.split(':')[0]
        return any(
            model_id in name or model_base in name
            for name in downloaded_names
        )
    except Exception:
        return False


def get_extraction_prompt(language: str = "German") -> str:
    """
    Get the extraction prompt for Ollama models

    Args:
        language: Primary language of the brochure

    Returns:
        Prompt string
    """
    if language == "German":
        return """Analyze this German supermarket brochure page and extract ALL product deals.

For EACH product you see, extract:
- product_name: Full product name (in German)
- price: Current price (number only, e.g., "2.99")
- original_price: Original price if shown (number only)
- discount: Discount percentage or amount if shown
- unit: Package size/weight (e.g., "500 g", "1 L")
- brand: Brand name if visible

Return ONLY a valid JSON array with all products. Example format:
[
  {
    "product_name": "Coca-Cola",
    "price": "1.99",
    "unit": "1.5 L",
    "brand": "Coca-Cola"
  },
  {
    "product_name": "Nutella",
    "price": "3.49",
    "original_price": "4.99",
    "discount": "30%",
    "unit": "450 g",
    "brand": "Ferrero"
  }
]

Extract ALL products visible on the page. Return ONLY the JSON array, no other text."""
    else:
        return f"""Analyze this {language} supermarket brochure page and extract ALL product deals.

For EACH product, extract: product_name, price, original_price (if shown), discount (if shown), unit, brand (if visible).

Return ONLY a valid JSON array. Extract ALL products on the page."""


def extract_with_ollama(
    image_array: np.ndarray,
    model_id: str = "llava:7b-v1.6",
    language: str = "German"
) -> Dict:
    """
    Extract product information using Ollama VLM

    Args:
        image_array: Image as numpy array
        model_id: Ollama model identifier
        language: Primary language in brochure

    Returns:
        Dictionary with extracted deals and metadata
    """
    try:
        import ollama
    except ImportError:
        raise ImportError(
            "Ollama Python package not installed. "
            "Install with: pip install ollama"
        )

    # Convert numpy array to PIL Image
    if len(image_array.shape) == 2:
        pil_image = Image.fromarray(image_array)
    else:
        pil_image = Image.fromarray(image_array)

    # Convert to base64 for Ollama
    buffered = BytesIO()
    pil_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Get extraction prompt
    prompt = get_extraction_prompt(language)

    # Check if model is downloaded
    if not check_model_downloaded(model_id):
        print(f"⬇️  Downloading {model_id} model (first time only)...")
        print(f"This may take a few minutes depending on your connection...")

    try:
        # Call Ollama API
        response = ollama.generate(
            model=model_id,
            prompt=prompt,
            images=[img_base64],
            stream=False,
            options={
                "temperature": 0.1,  # Low temperature for consistent extraction
                "num_predict": 2048  # Max tokens for response
            }
        )

        # Extract response text
        response_text = response['response']

        # Try to parse JSON from response
        deals = parse_json_from_response(response_text)

        if not deals:
            return {
                "deals": [],
                "total_products": 0,
                "extraction_method": f"Ollama {model_id}",
                "status": "error",
                "error": "No valid products extracted"
            }

        # Calculate confidence based on completeness
        avg_confidence = calculate_confidence(deals)

        return {
            "deals": deals,
            "total_products": len(deals),
            "average_confidence": avg_confidence,
            "extraction_method": f"Ollama {model_id}",
            "model_info": {
                "model": model_id,
                "provider": "Ollama (Local)"
            },
            "status": "success"
        }

    except Exception as e:
        error_msg = str(e)

        # Provide helpful error messages
        if "model" in error_msg.lower() and "not found" in error_msg.lower():
            error_msg = f"Model {model_id} not found. It will be downloaded automatically on first use."

        return {
            "deals": [],
            "total_products": 0,
            "extraction_method": f"Ollama {model_id}",
            "status": "error",
            "error": error_msg
        }


def parse_json_from_response(text: str) -> List[Dict]:
    """
    Parse JSON array from LLM response

    Args:
        text: Response text that may contain JSON

    Returns:
        List of product dictionaries
    """
    # Try to find JSON array in the response
    import re

    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Try to find JSON array
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_match:
        try:
            deals = json.loads(json_match.group(0))
            if isinstance(deals, list):
                return deals
        except json.JSONDecodeError:
            pass

    # Try parsing the entire text
    try:
        deals = json.loads(text)
        if isinstance(deals, list):
            return deals
    except json.JSONDecodeError:
        pass

    return []


def calculate_confidence(deals: List[Dict]) -> float:
    """
    Calculate average confidence based on completeness of extracted data

    Args:
        deals: List of extracted product dictionaries

    Returns:
        Average confidence score (0.0 to 1.0)
    """
    if not deals:
        return 0.0

    total_confidence = 0.0

    for deal in deals:
        confidence = 0.0

        # Product name is essential (40% weight)
        if deal.get('product_name'):
            confidence += 0.4

        # Price is essential (40% weight)
        if deal.get('price'):
            confidence += 0.4

        # Unit adds confidence (10% weight)
        if deal.get('unit'):
            confidence += 0.1

        # Brand or discount adds confidence (10% weight)
        if deal.get('brand') or deal.get('discount'):
            confidence += 0.1

        total_confidence += confidence

    return total_confidence / len(deals)


def pull_model(model_id: str, progress_callback=None) -> bool:
    """
    Download an Ollama model

    Args:
        model_id: Ollama model identifier
        progress_callback: Optional callback for progress updates

    Returns:
        True if successful
    """
    try:
        import ollama

        if progress_callback:
            progress_callback(f"Downloading {model_id}...")

        # Pull the model
        ollama.pull(model_id)

        if progress_callback:
            progress_callback(f"✓ {model_id} downloaded successfully!")

        return True

    except Exception as e:
        if progress_callback:
            progress_callback(f"✗ Download failed: {str(e)}")
        return False


def delete_model(model_id: str) -> bool:
    """
    Delete an Ollama model

    Args:
        model_id: Ollama model identifier

    Returns:
        True if successful
    """
    try:
        import ollama
        ollama.delete(model_id)
        return True
    except Exception:
        return False


# Test function
if __name__ == "__main__":
    print("Testing Ollama VLM Extractor")
    print("=" * 50)

    # Check if Ollama is available
    if check_ollama_available():
        print("✓ Ollama service is running")

        # List available models
        models = get_available_ollama_models()
        print("\nAvailable models:")
        for model in models:
            status = "✓ Downloaded" if model['downloaded'] else "○ Not downloaded"
            print(f"  {status} {model['name']}")
            print(f"    Model ID: {model['model_id']}")
            print(f"    Size: {model['size']}, Speed: {model['speed']}")
    else:
        print("✗ Ollama service is not running")
        print("  Start with: brew services start ollama")
