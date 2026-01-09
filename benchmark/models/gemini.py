import os
import json
import pathlib
from typing import List, Dict, Any, Optional
from google import genai
from .base import BaseOCRModel

class GeminiModel(BaseOCRModel):
    """
    Wrapper for Google Gemini API.
    """
    PROMPT = """You are analyzing a supermarket brochure page in German.

Extract ALL product deals. For each product, identify:
1. **Product Name**
2. **Price** (format: "X.XX")
3. **bbox**: Bounding box in normalized coordinates [ymin, xmin, ymax, xmax]
   - SCALE: 0 to 1000
   - ORDER: y_min, x_min, y_max, x_max
   - BOXING RULE: Enclose the ENTIRE product card/area (including image, text, price and promotional background).

Return ONLY a JSON array:
[
  {
    "product_name": "...",
    "price": "...",
    "bbox": [ymin, xmin, ymax, xmax]
  }
]
"""

    def __init__(self, api_key: str, model_id: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self._model_id = model_id
        self.client = genai.Client(api_key=api_key)

    @property
    def model_name(self) -> str:
        return f"Gemini-{self._model_id}"

    def _strip_markdown_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1 :]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        image_bytes = pathlib.Path(image_path).read_bytes()
        try:
            response = self.client.models.generate_content(
                model=self._model_id,
                contents=[{"text": self.PROMPT}, {"inline_data": {"mime_type": "image/png", "data": image_bytes}}],
            )
            raw_text = response.text
            print(f"DEBUG {self._model_id}: Raw response length: {len(raw_text)}")
            if len(raw_text) < 100:
                print(f"DEBUG {self._model_id}: Raw text: {raw_text}")
            clean_text = self._strip_markdown_fences(raw_text)
            deals = json.loads(clean_text)
            
            # Convert [ymin, xmin, ymax, xmax] 0-1000 -> [xmin, ymin, xmax, ymax] 0-1
            converted = []
            for d in deals:
                bb = d.get("bbox")
                if bb and len(bb) == 4:
                    # ymin, xmin, ymax, xmax -> xmin, ymin, xmax, ymax
                    new_bb = [bb[1]/1000.0, bb[0]/1000.0, bb[3]/1000.0, bb[2]/1000.0]
                    d["bbox"] = new_bb
                    print(f"DEBUG {self._model_id}: Predicted x1={new_bb[0]:.3f}, y1={new_bb[1]:.3f}, x2={new_bb[2]:.3f}, y2={new_bb[3]:.3f} for {d.get('product_name')}")
                converted.append(d)
            return converted
            
        except Exception as e:
            print(f"Error calling Gemini {self._model_id}: {e}")
            return []
