import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from services.model_router import extract_deals, ExtractionMethod

FEATURES_FILE = Path(__file__).parent.parent / "extractors" / "features.yaml"

class FeatureRouter:
    _features: Dict[str, Any] = {}

    @classmethod
    def load_config(cls):
        if not FEATURES_FILE.exists():
            return
        with open(FEATURES_FILE, "r") as f:
            config = yaml.safe_load(f)
            cls._features = config.get("features", {})

    @classmethod
    def get_features(cls) -> Dict[str, Any]:
        if not cls._features:
            cls.load_config()
        return cls._features

    @classmethod
    def save_config(cls):
        """Persist current configuration to YAML file"""
        try:
             # Ensure directory exists
            FEATURES_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            with open(FEATURES_FILE, "w") as f:
                yaml.dump({"features": cls._features}, f, sort_keys=False, indent=2)
            print(f"[FeatureRouter] Saved config to {FEATURES_FILE}")
        except Exception as e:
            print(f"[FeatureRouter] Failed to save config: {e}")

    @classmethod
    def update_model_for_feature(cls, feature_key: str, model_id: str):
        cls.get_features() # Ensure loaded
        if feature_key in cls._features:
            # Validate simple rules
            if "allowed_models" in cls._features[feature_key]:
                if model_id not in cls._features[feature_key]["allowed_models"]:
                    # Optional: Could raise error, but for now we allow override or add it to allowed
                    if model_id not in cls._features[feature_key]["allowed_models"]:
                         cls._features[feature_key]["allowed_models"].append(model_id)

            cls._features[feature_key]["default_model"] = model_id
            cls.save_config()
            return True
        return False

    @classmethod
    async def process_feature(
        cls, 
        feature_key: str, 
        file_path: str,
        store_name: str = "Unknown",
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        features = cls.get_features()
        feature_config = features.get(feature_key)
        
        if not feature_config:
            raise ValueError(f"Unknown feature: {feature_key}")

        model_id = model_override or feature_config.get("default_model")
        
        # Determine Method based on model_id
        method = ExtractionMethod.GEMINI
        if "llava" in model_id or "qwen" in model_id or "llama" in model_id:
             method = ExtractionMethod.LOCAL_VLM
        elif "ocr" in model_id:
             method = ExtractionMethod.OCR_PIPELINE
        
        # Select Prompt (In a real implementation, this would load from a prompt registry)
        # For now, we rely on model_router's default prompts unless we pass a custom one.
        # Ideally, we pass the "task instruction" to extract_deals if refactored further.
        
        print(f"DEBUG: Processing Feature '{feature_config['name']}' using Model '{model_id}'")

        return await extract_deals(
            file_path=file_path,
            store_name=store_name,
            method=method,
            model_id=model_id
        )

feature_router = FeatureRouter()
