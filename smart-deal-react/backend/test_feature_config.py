import sys
import os
import asyncio

# Add backend directory to sys.path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.feature_router import feature_router

def test_feature_config():
    print("Testing Feature Router Configuration...")
    
    # 1. Load config
    features = feature_router.get_features()
    if not features:
        print("❌ Failed to load features.yaml")
        sys.exit(1)
    print(f"✅ Loaded {len(features)} features")
    
    # 2. Check defaults
    expected_defaults = {
        "invoice_parser": "gemini-2.5-pro",
        "discount_brochure": "gemini-2.5-flash-lite",
        "member_card": "llava:7b"
    }
    
    for key, expected_model in expected_defaults.items():
        config = features.get(key)
        if not config:
             print(f"❌ Missing feature: {key}")
             sys.exit(1)
        
        actual_model = config.get("default_model")
        if actual_model == expected_model:
            print(f"✅ Feature '{key}' maps to '{actual_model}' correctly")
        else:
            print(f"❌ Feature '{key}' maps to '{actual_model}', expected '{expected_model}'")
            sys.exit(1)

    print("All configuration checks passed!")

if __name__ == "__main__":
    test_feature_config()
