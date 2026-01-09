import os
import json
import pathlib
from google import genai

def debug_gemini(api_key, model_id, image_path):
    client = genai.Client(api_key=api_key)
    prompt = """Extract ALL product deals from this image. 
Return ONLY a JSON array of objects with keys: product_name, price, bbox [x_min, y_min, x_max, y_max] (normalized 0-1)."""
    
    image_bytes = pathlib.Path(image_path).read_bytes()
    response = client.models.generate_content(
        model=model_id,
        contents=[prompt, {"inline_data": {"mime_type": "image/png", "data": image_bytes}}]
    )
    print(f"\n--- {model_id} RAW RESPONSE ---")
    print(response.text)
    print("------------------------------")

if __name__ == "__main__":
    key = "AIzaSyAAYImGiSbT_emoKbCxTolGQ0KDEHBsldU"
    img = r"c:\Users\zack\Downloads\smart-deal-finder\data\images_uniform\rewe\rewe_10112025_page_1.png"
    debug_gemini(key, "gemini-2.0-flash", img)
    # debug_gemini(key, "gemini-1.5-pro", img)
