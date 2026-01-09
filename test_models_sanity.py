import os
import sys
from benchmark.models import (
    GeminiModel, PaddleOCRModel, QwenOCRModel, DeepSeekOCRModel, 
    MockModel, GotOCRModel, Florence2Model, InternVL2Model
)

def test_model(model_instance, test_image):
    print(f"\n" + "="*50)
    print(f" TESTING MODEL: {model_instance.model_name}")
    print("="*50)
    try:
        results = model_instance.extract_deals(test_image)
        print(f"  [SUCCESS] Extracted {len(results)} items.")
        return True
    except Exception as e:
        print(f"  [FAILED] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyAAYImGiSbT_emoKbCxTolGQ0KDEHBsldU")
    test_image = r"c:\Users\zack\Downloads\smart-deal-finder\data\images_uniform\rewe\rewe_10112025_page_1.png"

    if not os.path.exists(test_image):
        print(f"Error: Test image not found at {test_image}")
        return

    models = [
        # GeminiModel(api_key, model_id="gemini-2.0-flash"),
        PaddleOCRModel(),
        QwenOCRModel(),
        GotOCRModel(),
        Florence2Model(),
        InternVL2Model(),
        DeepSeekOCRModel()
    ]

    status = {}
    for model in models:
        ok = test_model(model, test_image)
        status[model.model_name] = "OK" if ok else "FAILED"

    print("\n" + "="*30)
    print("SANITY CHECK SUMMARY")
    print("="*30)
    for m, s in status.items():
        print(f"{m:<30}: {s}")

if __name__ == "__main__":
    main()
