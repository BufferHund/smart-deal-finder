import os
import json
import base64
import torch
from typing import List, Dict, Any, Optional
from transformers import AutoProcessor, AutoModelForCausalLM, Qwen2VLForConditionalGeneration, AutoModel
from .base import BaseOCRModel

class QwenOCRModel(BaseOCRModel):
    def __init__(self, model_id: str = "JackChew/Qwen2-VL-2B-OCR"):
        self.model_id = model_id
        self._model = None
        self._processor = None

    @property
    def model_name(self) -> str:
        return f"Qwen-Local-{self.model_id.split('/')[-1]}"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            print(f"\n[INFO] Checking/Downloading model: {self.model_id}")
            snapshot_download(repo_id=self.model_id)
            self._model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_id, torch_dtype="auto", device_map="auto", trust_remote_code=True
            )
            self._processor = AutoProcessor.from_pretrained(self.model_id)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        from qwen_vl_utils import process_vision_info
        prompt = "Extract ALL product deals from this page as a JSON array with: product_name, price, unit, bbox [x1, y1, x2, y2] (0-1)."
        messages = [{"role": "user", "content": [{"type": "image", "image": image_path}, {"type": "text", "text": prompt}]}]
        text = self._processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self._processor(text=[text], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt").to(self._model.device)
        generated_ids = self._model.generate(**inputs, max_new_tokens=1024)
        output_text = self._processor.batch_decode(generated_ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
        try:
            start = output_text.find("[")
            end = output_text.rfind("]") + 1
            if start != -1 and end != -1: return json.loads(output_text[start:end])
        except: pass
        return []

class GotOCRModel(BaseOCRModel):
    def __init__(self, model_id: str = "stepfun-ai/GOT-OCR2_0"):
        self.model_id = model_id
        self._model = None
        self._tokenizer = None

    @property
    def model_name(self) -> str:
        return "GOT-OCR2.0"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=self.model_id)
            self._model = AutoModel.from_pretrained(self.model_id, trust_remote_code=True, low_cpu_mem_usage=True, device_map="auto").eval()
            from transformers import AutoTokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        # GOT-OCR2_0 uses a custom chat method
        res = self._model.chat(self._tokenizer, image_path, mode='fine-grained')
        # Post-process GOT output into our JSON format (heuristic)
        print(f"GOT-OCR Output: {res[:100]}...")
        return []

class Florence2Model(BaseOCRModel):
    def __init__(self, model_id: str = "microsoft/Florence-2-large"):
        self.model_id = model_id
        self._model = None
        self._processor = None

    @property
    def model_name(self) -> str:
        return "Florence-2-Large"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=self.model_id)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True, device_map="auto").eval()
            self._processor = AutoProcessor.from_pretrained(self.model_id, trust_remote_code=True)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        from PIL import Image
        image = Image.open(image_path).convert("RGB")
        # Task for detailed OCR with regions
        task_prompt = "<OCR_WITH_REGION>"
        inputs = self._processor(text=task_prompt, images=image, return_tensors="pt").to(self._model.device)
        generated_ids = self._model.generate(input_ids=inputs["input_ids"], pixel_values=inputs["pixel_values"], max_new_tokens=1024, num_beams=3)
        generated_text = self._processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self._processor.post_process_generation(generated_text, task=task_prompt, image_size=(image.width, image.height))
        
        # Convert Florence output to our common format
        results = []
        if task_prompt in parsed_answer:
            data = parsed_answer[task_prompt]
            # data is usually {'quad_boxes': [...], 'labels': [...]}
            # We map this to product blocks heuristically or just return as is
            for i in range(len(data.get('labels', []))):
                results.append({
                    "product_name": data['labels'][i],
                    "bbox": [c/1000.0 for c in data['quad_boxes'][i]] if 'quad_boxes' in data else [0,0,1,1]
                })
        return results

class InternVL2Model(BaseOCRModel):
    def __init__(self, model_id: str = "OpenGVLab/InternVL2-2B"):
        self.model_id = model_id
        self._model = None
        self._tokenizer = None

    @property
    def model_name(self) -> str:
        return "InternVL2-2B"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=self.model_id)
            self._model = AutoModel.from_pretrained(self.model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="auto").eval()
            from transformers import AutoTokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        # InternVL2 specific inference (simplified for the wrapper)
        from PIL import Image
        pixel_values = self._load_image(image_path)
        question = "Extract all products as JSON list with: product_name, price, unit, bbox [x1, y1, x2, y2]."
        response, history = self._model.chat(self._tokenizer, pixel_values, question, generation_config={"max_new_tokens": 1024})
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end != -1: return json.loads(response[start:end])
        except: pass
        return []

    def _load_image(self, image_file, input_size=448, max_num=6):
        from torchvision.transforms import T
        from torchvision.transforms.functional import InterpolationMode
        from PIL import Image
        image = Image.open(image_file).convert('RGB')
        transform = T.Compose([
            T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225))
        ])
        pixel_values = transform(image).unsqueeze(0).to(torch.bfloat16).to(self._model.device)
        return pixel_values

class DeepSeekOCRModel(BaseOCRModel):
    def __init__(self, model_id: str = "deepseek-ai/DeepSeek-OCR"):
        self.model_id = model_id
        self._model = None
        self._tokenizer = None

    @property
    def model_name(self) -> str:
        return "DeepSeek-OCR-Local"

    def _init_model(self):
        if self._model is None:
            from huggingface_hub import snapshot_download
            snapshot_download(repo_id=self.model_id)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_id, trust_remote_code=True, torch_dtype=torch.bfloat16, device_map="auto").eval()
            from transformers import AutoTokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)

    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        self._init_model()
        return []

class MockModel(BaseOCRModel):
    @property
    def model_name(self) -> str:
        return "MockModel (Test Only)"
    def extract_deals(self, image_path: str) -> List[Dict[str, Any]]:
        return [{"product_name": "Local Mock Product", "price": "1.99", "bbox": [0.1, 0.1, 0.3, 0.3]}]
