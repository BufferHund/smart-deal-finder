"""Gemini AI-powered product extraction"""

import json
import base64
from typing import List, Dict, Optional
from PIL import Image
import io


def encode_image_to_base64(image_array) -> str:
    """
    Convert image array to base64 string for Gemini API

    Args:
        image_array: numpy array of image

    Returns:
        Base64 encoded string
    """
    from PIL import Image

    # Convert to PIL Image
    if len(image_array.shape) == 2:  # Grayscale
        pil_image = Image.fromarray(image_array)
    else:  # RGB/BGR
        pil_image = Image.fromarray(image_array)

    # Convert to bytes
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()

    # Encode to base64
    return base64.b64encode(image_bytes).decode('utf-8')


def extract_with_gemini(
    image_array,
    api_key: str,
    model: str = "gemini-2.5-pro",
    language: str = "German"
) -> Dict:
    """
    Extract product information using Gemini AI

    Args:
        image_array: Image as numpy array
        api_key: Google AI Studio API key
        model: Gemini model name
        language: Primary language in brochure

    Returns:
        Dictionary with extracted deals
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "Google Generative AI library not installed. "
            "Install with: pip install google-generativeai"
        )

    # Configure API
    genai.configure(api_key=api_key)

    # Model name handling - remove "models/" prefix if present
    # Google AI Studio API expects model names without prefix
    model_name = model.replace("models/", "") if model.startswith("models/") else model

    # Create model instance
    model_instance = genai.GenerativeModel(model_name)

    # Convert image to PIL
    from PIL import Image
    if len(image_array.shape) == 2:
        pil_image = Image.fromarray(image_array)
    else:
        pil_image = Image.fromarray(image_array)

    # Craft prompt
    prompt = f"""You are analyzing a supermarket brochure page in {language}.

Extract ALL product deals from this image. For each product, identify:

1. **Product Name**: Full product name including brand
2. **Price**: The main selling price (in euros, format: "X.XX")
3. **Discount**: Discount percentage if shown (format: "XX" without %)
4. **Unit**: Product size/quantity (e.g., "500 g", "1 L", "750 ml")
5. **Original Price**: Original price before discount if shown

IMPORTANT RULES:
- Extract information from EACH visible product/deal on the page
- Group information by product card/region (don't mix products)
- Only extract text that is clearly visible and readable
- For prices, include ONLY the numeric value (e.g., "17.99" not "€17.99")
- For discounts, include ONLY the number (e.g., "20" not "-20%")
- If information is not visible or unclear, use null
- Pay special attention to product cards, promotional boxes, and price tags

Return ONLY a JSON array with this EXACT structure:
[
  {{
    "product_name": "Brand ProductName",
    "price": "X.XX",
    "discount": "XX" or null,
    "unit": "XXX g/ml/L/kg" or null,
    "original_price": "X.XX" or null
  }}
]

Example output:
[
  {{
    "product_name": "Baileys Irish Cream",
    "price": "17.99",
    "discount": null,
    "unit": "700 ml",
    "original_price": null
  }},
  {{
    "product_name": "Landliebe Joghurt",
    "price": "1.49",
    "discount": "20",
    "unit": "500 g",
    "original_price": "1.99"
  }}
]

Return ONLY the JSON array, no other text or explanation."""

    # Generate content
    print(f"DEBUG: Calling Gemini API (Model: {model_name})...")
    response = model_instance.generate_content([prompt, pil_image])
    print("DEBUG: Gemini API Response Response Received.")

    # Parse response
    response_text = response.text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith('```'):
        # Remove first line (```json or ```)
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])  # Remove first and last line

    print(f"DEBUG: Gemini Raw JSON Response:\n{response_text}") # Expose full data log

    # Parse JSON
    try:
        deals_data = json.loads(response_text)
        print(f"DEBUG: Successfully parsed {len(deals_data)} deals from Gemini.")
    except json.JSONDecodeError as e:
        print(f"DEBUG: Failed to decode JSON. Response was: {response_text}")
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    except Exception as e:
        print(f"DEBUG: Unexpected error in extraction: {e}")
        raise e

    # Convert to our format
    deals = []
    for deal_data in deals_data:
        deal = {
            'product_name': deal_data.get('product_name'),
            'price': deal_data.get('price'),
            'discount': deal_data.get('discount'),
            'unit': deal_data.get('unit'),
            'original_price': deal_data.get('original_price'),
            'category': deal_data.get('category', 'Other'),
            'image_url': None, # Placeholder for Phase 8.1
            'confidence': 0.95,  # Gemini is generally high confidence
            'source': 'gemini',
            'model': model
        }
        deals.append(deal)

    return {
        'deals': deals,
        'num_deals': len(deals),
        'model': model,
        'source': 'gemini'
    }


def test_gemini_connection(api_key: str) -> bool:
    """
    Test if Gemini API key is valid

    Args:
        api_key: Google AI Studio API key

    Returns:
        True if connection successful
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Try to list models
        models = genai.list_models()
        return True
    except Exception as e:
        return False


def get_available_models(api_key: str) -> List[str]:
    """
    Get list of available Gemini models

    Args:
        api_key: Google AI Studio API key

    Returns:
        List of model names
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        models = genai.list_models()
        model_names = []

        for model in models:
            # Only include models that support vision
            if 'generateContent' in model.supported_generation_methods:
                model_names.append(model.name.replace('models/', ''))

        return model_names
    except Exception:
        # Return default models if API call fails (Gemini 2.5 series)
        return ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-2.5-flash-lite']
