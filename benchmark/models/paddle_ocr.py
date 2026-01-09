import torch
from typing import List, Dict, Any, Optional
from transformers import AutoProcessor, AutoModelForCausalLM
from .base import BaseOCRModel

class PaddleOCRModel(BaseOCRModel):
    """
    Wrapper for PaddleOCR-VL (PaddlePaddle/PaddleOCR-VL).
    """
    def __init__(self, model_id: str = "PaddlePaddle/PaddleOCR-VL"):
        self.model_id = model_id
        self._model = None
        self._processor = None

    @property
    def model_name(self) -> str:
        return f"PaddleOCR-VL-{self.model_id.split('/')[-1]}"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            print(f"\n[INFO] Checking/Downloading model: {self.model_id}")
            snapshot_download(repo_id=self.model_id)

            print(f"Loading local model into memory: {self.model_id}...")
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                trust_remote_code=True, 
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32, 
                device_map="auto"
            )
            self._processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        print(f"PaddleOCR-VL ({self.model_id}) currently in skeletal local mode.")
        return []
