import os
import json
import base64
import re
import requests
import sys
import numpy as np
import time
from pathlib import Path
from difflib import SequenceMatcher
from tqdm import tqdm

# ================= 配置区域 =================
TEST_DATA_ROOT = "images_uniform" 

# 阈值设置
IOU_THRESHOLD = 0.5
NAME_MATCH_THRESHOLD = 0.5

# 提示词 (保持与训练一致)
SYSTEM_PROMPT = """You are analyzing a supermarket brochure page in German.
Extract ALL product deals from this image.
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
Return ONLY the JSON array, no other text or explanation."""

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

# ================= API 客户端实现 =================

class BaseClient:
    def __init__(self, model_name, api_key=None, base_url=None):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url

    def test_connection(self):
        """发送一个极简请求验证 Key"""
        raise NotImplementedError

    def query(self, image_path, prompt):
        raise NotImplementedError

class OllamaClient(BaseClient):
    def __init__(self, model_name):
        super().__init__(model_name, None, "http://localhost:11434")

    def test_connection(self):
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=2)
            # 简单生成测试
            self.query_text_only("hi")
            return True, "Ollama connected."
        except Exception as e:
            return False, str(e)

    def query_text_only(self, text):
        payload = {"model": self.model_name, "messages": [{"role": "user", "content": text}], "stream": False}
        requests.post(f"{self.base_url}/api/chat", json=payload).raise_for_status()

    def query(self, image_path, prompt):
        b64 = encode_image_to_base64(image_path)
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt, "images": [b64]}],
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096}
        }
        res = requests.post(f"{self.base_url}/api/chat", json=payload)
        res.raise_for_status()
        return res.json()['message']['content']

class GeminiClient(BaseClient):
    def __init__(self, model_name, api_key):
        super().__init__(model_name, api_key, "https://generativelanguage.googleapis.com/v1beta/models")

    def test_connection(self):
        try:
            # 简单的文本测试
            url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code != 200:
                return False, f"HTTP {res.status_code}: {res.text}"
            return True, "Gemini connected."
        except Exception as e:
            return False, str(e)

    def query(self, image_path, prompt):
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"
        
        # Gemini 需要这种 mime_type 格式
        mime_type = "image/jpeg"
        if image_path.lower().endswith(".png"): mime_type = "image/png"
        
        b64 = encode_image_to_base64(image_path)
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {
                        "mime_type": mime_type,
                        "data": b64
                    }}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json" # Gemini 1.5 支持强制 JSON
            }
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json()['candidates'][0]['content']['parts'][0]['text']

class SiliconFlowClient(BaseClient):
    def __init__(self, model_name, api_key):
        # SiliconFlow 兼容 OpenAI 格式
        super().__init__(model_name, api_key, "https://api.siliconflow.cn/v1/chat/completions")

    def test_connection(self):
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }
            res = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            if res.status_code != 200:
                return False, f"HTTP {res.status_code}: {res.text}"
            return True, "SiliconFlow connected."
        except Exception as e:
            return False, str(e)

    def query(self, image_path, prompt):
        b64 = encode_image_to_base64(image_path)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        
        # OpenAI Vision 格式
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
            "response_format": {"type": "json_object"} # 强制 JSON
        }
        
        res = requests.post(self.base_url, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']

# ================= 工具函数 =================

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def setup_client_interactive():
    print(f"{Colors.HEADER}=== Step 1: Select Provider ==={Colors.END}")
    print("1. Local Ollama (Free, Local)")
    print("2. Google Gemini (Cloud, Requires API Key)")
    print("3. SiliconFlow (Cloud, Requires API Key, Qwen/DeepSeek)")
    
    while True:
        choice = input("Select provider (1-3): ").strip()
        
        # --- Option 1: Ollama ---
        if choice == '1':
            try:
                resp = requests.get("http://localhost:11434/api/tags", timeout=2)
                models = [m['name'] for m in resp.json()['models']]
                print(f"\nAvailable Local Models:")
                for i, m in enumerate(models):
                    print(f"  [{i+1}] {m}")
                midx = int(input(f"Select model (1-{len(models)}): ")) - 1
                return OllamaClient(models[midx])
            except Exception as e:
                print(f"{Colors.FAIL}Could not connect to Ollama: {e}{Colors.END}")
                return None

        # --- Option 2: Gemini ---
        elif choice == '2':
            api_key = input("Enter Google Gemini API Key: ").strip()
            print("\nRecommended Gemini Models:")
            print("  1. gemini-1.5-flash (Fast, Cheap)")
            print("  2. gemini-1.5-pro (High Accuracy)")
            m_choice = input("Select model (1/2): ").strip()
            model = "gemini-1.5-flash" if m_choice == '1' else "gemini-1.5-pro"
            
            client = GeminiClient(model, api_key)
            print(f"Testing connection to {model}...")
            ok, msg = client.test_connection()
            if ok:
                print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
                return client
            else:
                print(f"{Colors.FAIL}❌ Connection failed: {msg}{Colors.END}")
                if input("Try again? (y/n): ").lower() != 'y': return None

        # --- Option 3: SiliconFlow ---
        elif choice == '3':
            api_key = input("Enter SiliconFlow API Key: ").strip()
            print("\nRecommended SiliconFlow Models:")
            print("  1. Qwen/Qwen2.5-VL-72B-Instruct (SOTA Open Source)")
            print("  2. Pro/Qwen/Qwen2-VL-7B-Instruct (Faster)")
            print("  3. deepseek-ai/deepseek-vl2 (If available)")
            
            m_choice = input("Select model (1-3) or type custom: ").strip()
            if m_choice == '1': model = "Qwen/Qwen2.5-VL-72B-Instruct"
            elif m_choice == '2': model = "Pro/Qwen/Qwen2-VL-7B-Instruct"
            elif m_choice == '3': model = "deepseek-ai/deepseek-vl2"
            else: model = m_choice
            
            client = SiliconFlowClient(model, api_key)
            print(f"Testing connection to {model}...")
            ok, msg = client.test_connection()
            if ok:
                print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
                return client
            else:
                print(f"{Colors.FAIL}❌ Connection failed: {msg}{Colors.END}")
                if input("Try again? (y/n): ").lower() != 'y': return None

# ================= 数据与评估逻辑 (复用之前的稳健代码) =================

def load_dataset_from_structure(root_path):
    dataset = []
    root = Path(root_path)
    print(f"\n{Colors.HEADER}=== Step 2: Loading Data ==={Colors.END}")
    print(f"📂 Scanning: {root_path}...")
    
    image_files = list(root.rglob('*.png')) + list(root.rglob('*.jpg'))
    for image_path in image_files:
        image_folder = image_path.parent
        folder_name = image_folder.name
        if folder_name.endswith('_annotated'): continue
        json_path = image_folder.parent / f"{folder_name}_annotated" / f"{image_path.stem}.json"

        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if data: dataset.append({"image_path": str(image_path), "gt_data": data})
            except: continue
    
    np.random.shuffle(dataset)
    return dataset

def clean_json_output(text):
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```', '', text)
    match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
    if match: json_str = match.group(0)
    else: json_str = text
    try:
        data = json.loads(json_str)
        if isinstance(data, dict): return [data]
        return data
    except: return None

def normalize_price(price_str):
    if not price_str: return ""
    return str(price_str).replace("€", "").replace("$", "").replace(",", ".").strip()

def calculate_iou(box1, box2):
    if not box1 or not box2: return 0.0
    try:
        b1, b2 = [float(x) for x in box1], [float(x) for x in box2]
    except: return 0.0
    x_left, y_top = max(b1[0], b2[0]), max(b1[1], b2[1])
    x_right, y_bottom = min(b1[2], b2[2]), min(b1[3], b2[3])
    if x_right < x_left or y_bottom < y_top: return 0.0
    intersection = (x_right - x_left) * (y_bottom - y_top)
    union = ((b1[2]-b1[0])*(b1[3]-b1[1])) + ((b2[2]-b2[0])*(b2[3]-b2[1])) - intersection
    return intersection / union if union > 0 else 0.0

def evaluate_metrics(predictions, ground_truths):
    stats = {
        "total_gt": 0, "total_pred": 0, "correct_matches": 0,
        "price_correct": 0, "bbox_correct": 0, "bbox_iou_sum": 0.0
    }
    for pred_list, gt_list in zip(predictions, ground_truths):
        if gt_list is None: gt_list = []
        if pred_list is None: pred_list = []
        stats["total_gt"] += len(gt_list)
        stats["total_pred"] += len(pred_list)
        
        matched_indices = set()
        for p_item in pred_list:
            p_name = str(p_item.get("product_name", p_item.get("name", ""))).lower()
            p_price = normalize_price(p_item.get("price", ""))
            p_bbox = p_item.get("bbox", p_item.get("box", []))

            best_score, best_idx = 0, -1
            for i, gt_item in enumerate(gt_list):
                if i in matched_indices: continue
                g_name = str(gt_item.get("product_name", gt_item.get("name", ""))).lower()
                score = SequenceMatcher(None, p_name, g_name).ratio()
                if score > best_score: best_score, best_idx = score, i
            
            if best_score > NAME_MATCH_THRESHOLD:
                stats["correct_matches"] += 1
                matched_indices.add(best_idx)
                gt_match = gt_list[best_idx]
                if p_price == normalize_price(gt_match.get("price", "")) and p_price:
                    stats["price_correct"] += 1
                iou = calculate_iou(p_bbox, gt_match.get("bbox", gt_match.get("box", [])))
                stats["bbox_iou_sum"] += iou
                if iou > IOU_THRESHOLD: stats["bbox_correct"] += 1

    tp = stats["correct_matches"]
    fp = stats["total_pred"] - tp
    fn = stats["total_gt"] - tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "F1 Score": f"{f1:.2%}",
        "Precision": f"{precision:.2%}",
        "Recall": f"{recall:.2%}",
        "Price Acc.": f"{stats['price_correct']/tp:.2%}" if tp else "0.00%",
        "BBox Acc.": f"{stats['bbox_correct']/tp:.2%}" if tp else "0.00%",
        "Mean IoU": f"{stats['bbox_iou_sum']/tp:.2f}" if tp else "0.00",
        "TP / GT": f"{tp} / {stats['total_gt']}"
    }

def main():
    # 1. 设置客户端 (包含测试连接)
    client = setup_client_interactive()
    if not client: return

    # 2. 加载数据
    if not os.path.exists(TEST_DATA_ROOT):
        print(f"❌ Error: {TEST_DATA_ROOT} not found.")
        return
    full_dataset = load_dataset_from_structure(TEST_DATA_ROOT)
    if not full_dataset: return

    # 3. 选择数量
    print(f"\n{Colors.HEADER}=== Step 3: Test Configuration ==={Colors.END}")
    count_in = input(f"Test how many images? (Enter for ALL {len(full_dataset)}): ").strip()
    test_data = full_dataset if count_in == "" else full_dataset[:int(count_in)]

    # 4. 运行
    preds, gts = [], []
    print(f"\n🚀 Running {client.model_name} on {len(test_data)} samples...")
    try:
        for item in tqdm(test_data):
            try:
                raw = client.query(item['image_path'], SYSTEM_PROMPT)
                preds.append(clean_json_output(raw))
            except Exception as e:
                print(f"\n⚠️ Error on {item['image_path']}: {e}")
                preds.append([])
            gts.append(item['gt_data'])
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted! Calculating partial results...")

    # 5. 报告
    print("\n📊 Calculating Metrics...")
    results = evaluate_metrics(preds, gts)
    print("\n" + "="*45)
    print(f" REPORT: {client.model_name}")
    print("="*45)
    for k, v in results.items():
        print(f" {k:<20} : {v}")
    print("="*45)

if __name__ == "__main__":
    main()
