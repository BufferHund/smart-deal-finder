# smart-deal-finder/dataset/gemini_batch_ls.py
"""
Process supermarket brochure images in bulk using Google Gemini
to extract product deals and format them for Label Studio annotations.
"""
import os
import json
import uuid
import pathlib
from google import genai


# Configurations
# Your Gemini API Key
GEMINI_API_KEY = "AIzaSyDnbd9a608PJBT5HBhb7GFSTRyHe9bfl3s"

# JSON exported from Label Studio
LS_EXPORT_PATH = "project-2-at-2025-11-15-22-54-bb446493.json"

# Output annotations path
OUTPUT_ANN_PATH = "ls_annotations_gemini.json"

# Base directory where brochure images are stored locally
BASE_IMAGE_DIR = "rewe"


# Gemini Client
client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT = f"""You are analyzing a supermarket brochure page in German.

Extract ALL product deals from this image. For each product, identify:

1. **Product Name**: Full product name including brand
2. **Price**: The main selling price (in euros, format: "X.XX")
3. **Discount**: Discount percentage if shown (format: "XX" without %)
4. **Unit**: Product size/quantity (e.g., "je 500-g-Pckg.", "je 1-l-Becher", "je 750 g")
5. **Original Price**: Original price before discount if shown
6. **bbox**: Bounding box of the product region in normalized coordinates  
   Format: `[x_min, y_min, x_max, y_max]`  
   - All values must be between **0 and 1**  
   - Coordinates refer to the **entire brochure page**, not cropped regions  
   - `x_min < x_max`, `y_min < y_max`  
   - Bounding box should tightly cover the product’s visual area (product card, price box, text, etc.)

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
    "unit": "je XXX g/ml/l/kg-XXX" or null,
    "original_price": "X.XX" or null,
    "bbox": [0.0, 0.0, 1.0, 1.0]
  }}
]

Example output:
[
  {{
    "product_name": "Baileys Irish Cream",
    "price": "17.99",
    "discount": null,
    "unit": "je 700-ml-Becher",
    "original_price": null,
    "bbox": [0.12, 0.30, 0.28, 0.71]
  }},
  {{
    "product_name": "Landliebe Joghurt",
    "price": "1.49",
    "discount": "20",
    "unit": "je 500-g-Dose",
    "original_price": "1.99",
    "bbox": [0.42, 0.18, 0.57, 0.55]
  }}
]

Return ONLY the JSON array, no other text or explanation."""


# Tools for processing

def strip_markdown_fences(text: str) -> str:
    """Remove markdown code fences from the text."""
    text = text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    return text.strip()


def call_gemini_for_brochure(image_path: str):
    """Read image and call Gemini to extract deals."""
    image_bytes = pathlib.Path(image_path).read_bytes()
    prompt = PROMPT

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": image_bytes
                        }
                    }
                ]
            }
        ],
    )

    raw_text = response.text
    clean_text = strip_markdown_fences(raw_text)

    try:
        deals = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"JSON extraction failed {e}")
        print("Raw output was:")
        print(raw_text)
        return []

    if not isinstance(deals, list):
        print("Model output is not a list as expected.")
        return []

    return deals


def convert_bbox_to_ls(bbox):
    """
    Gemini: [x_min, y_min, x_max, y_max] (0 to 1)
    Label Studio: x, y, width, height (0 to 100)
    """
    x_min, y_min, x_max, y_max = bbox
    return {
        "x": x_min * 100,
        "y": y_min * 100,
        "width": (x_max - x_min) * 100,
        "height": (y_max - y_min) * 100,
        "rotation": 0
    }


def build_ls_annotation_for_one_image(image_path_in_ls: str, deals: list, task_id: int | None = None):
    """
    Build Label Studio annotation object for one image.
    """
    results = []

    for deal in deals:
        bbox = deal.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        region_id = f"region-{uuid.uuid4().hex[:8]}"

        # bounding box
        ls_box = convert_bbox_to_ls(bbox)
        results.append({
            "id": region_id,
            "from_name": "deal",
            "to_name": "image",
            "type": "rectanglelabels",
            "value": {
                **ls_box,
                "rectanglelabels": ["Deal"]
            }
        })

        # fields
        for field in ["product_name", "price", "discount", "unit", "original_price"]:
            value = deal.get(field)
            text_value = "" if value is None else str(value)
            results.append({
                "id": region_id,
                "from_name": field,
                "to_name": "image",
                "type": "textarea",
                "value": {
                    "text": [text_value]
                }
            })

    ann_obj = {
        "data": {
            "image": image_path_in_ls
        },
        "annotations": [
            {
                "result": results
            }
        ]
    }

    if task_id is not None:
        ann_obj["id"] = task_id

    return ann_obj


def map_ls_image_to_local_path(ls_image_path: str) -> str:
    """
    Map Label Studio image path to local file system path.
    """
    filename = os.path.basename(ls_image_path)

    local_path = os.path.join(BASE_IMAGE_DIR, filename)

    real_name = filename.split("-", 1)[-1]
    local_path = os.path.join(BASE_IMAGE_DIR, real_name)

    return local_path


# Main processing function

def main():
    # Read tasks from Label Studio export
    with open(LS_EXPORT_PATH, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    all_annotations = []

    for i, task in enumerate(tasks, start=1):
        ls_image_path = task["image"]
        task_id = task.get("id")

        local_image_path = map_ls_image_to_local_path(ls_image_path)

        if not os.path.exists(local_image_path):
            print(f"!!! Cannot find picture from: {local_image_path}, skipping.")
            continue

        print(f"[{i}/{len(tasks)}] processing: {local_image_path}")

        deals = call_gemini_for_brochure(local_image_path)

        if not deals:
            print("!!! No deals extracted, skipping.")
            continue

        ann = build_ls_annotation_for_one_image(
            image_path_in_ls=ls_image_path,
            deals=deals,
            task_id=task_id
        )

        all_annotations.append(ann)

    # save all annotations to output file
    if all_annotations:
        with open(OUTPUT_ANN_PATH, "w", encoding="utf-8") as f:
            json.dump(all_annotations, f, indent=2, ensure_ascii=False)
        print(f"saved {len(all_annotations)} annotations to {OUTPUT_ANN_PATH}")
    else:
        print("No annotations to save.")


if __name__ == "__main__":
    main()