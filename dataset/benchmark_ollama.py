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
OLLAMA_BASE_URL = "http://localhost:11434"
TEST_DATA_ROOT = "images_uniform" 

# 阈值设置
IOU_THRESHOLD = 0.5
NAME_MATCH_THRESHOLD = 0.5
# ===========================================

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

def get_available_models():
    """从 Ollama 获取可用模型列表"""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m['name'] for m in resp.json()['models']]
            return models
        return []
    except:
        return []

def select_model_interactive():
    """交互式选择模型"""
    print(f"{Colors.HEADER}--- Step 1: Select Model ---{Colors.END}")
    models = get_available_models()
    
    if not models:
        print(f"{Colors.FAIL}❌ Could not connect to Ollama or no models found.{Colors.END}")
        print("Please check if 'ollama serve' is running.")
        sys.exit(1)

    print(f"Available local models:")
    for i, m in enumerate(models):
        print(f"  [{i+1}] {Colors.GREEN}{m}{Colors.END}")

    while True:
        choice = input(f"\nSelect model number (1-{len(models)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                print(f"✅ Selected: {Colors.BLUE}{selected}{Colors.END}")
                return selected
        print("Invalid selection. Please try again.")

def get_test_count_interactive(total_files):
    """交互式获取测试数量"""
    print(f"\n{Colors.HEADER}--- Step 2: Test Configuration ---{Colors.END}")
    print(f"Found {total_files} images in dataset.")
    
    while True:
        user_input = input(f"How many images to test? (Press Enter for ALL, or type number): ").strip()
        if user_input == "":
            print(f"✅ Testing {Colors.BLUE}ALL{Colors.END} images.")
            return total_files
        
        if user_input.isdigit():
            count = int(user_input)
            if 0 < count <= total_files:
                print(f"✅ Testing {Colors.BLUE}{count}{Colors.END} images.")
                return count
            else:
                print(f"Please enter a number between 1 and {total_files}.")
        else:
            print("Invalid input. Enter a number.")

def load_dataset_from_structure(root_path):
    dataset = []
    root = Path(root_path)
    print(f"\n{Colors.HEADER}--- Step 3: Loading Data ---{Colors.END}")
    print(f"📂 Scanning: {root_path}...")
    
    image_files = list(root.rglob('*.png')) + list(root.rglob('*.jpg'))
    
    for image_path in image_files:
        image_folder = image_path.parent
        folder_name = image_folder.name
        if folder_name.endswith('_annotated'): continue

        json_folder_name = f"{folder_name}_annotated"
        json_filename = image_path.stem + ".json"
        json_path = image_folder.parent / json_folder_name / json_filename

        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    annotation_data = json.load(f)
                
                # 修复: 过滤空 JSON
                if not annotation_data: continue

                dataset.append({
                    "image_path": str(image_path),
                    "gt_data": annotation_data,
                    "filename": image_path.name
                })
            except Exception:
                continue
    
    # 随机打乱以保证测试少样本时的多样性
    np.random.shuffle(dataset)
    return dataset

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def query_ollama(image_path, model, prompt):
    base64_image = encode_image_to_base64(image_path)
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": [base64_image]}],
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 4096}
    }
    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()
        return response.json()['message']['content']
    except Exception as e:
        print(f"\n❌ Error on {os.path.basename(image_path)}: {e}")
        return "[]"

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
        # 🛡️ Fix for NoneType error
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
    # 1. 选择模型
    selected_model = select_model_interactive()
    
    # 2. 加载数据
    if not os.path.exists(TEST_DATA_ROOT):
        print(f"{Colors.FAIL}Error: Directory '{TEST_DATA_ROOT}' not found.{Colors.END}")
        return
    
    full_dataset = load_dataset_from_structure(TEST_DATA_ROOT)
    if not full_dataset:
        print("No valid data found.")
        return

    # 3. 选择测试数量
    test_count = get_test_count_interactive(len(full_dataset))
    test_data = full_dataset[:test_count]

    # 4. 开始跑
    preds, gts = [], []
    print(f"\n{Colors.HEADER}--- Step 4: Starting Inference ---{Colors.END}")
    print(f"🚀 Model: {selected_model}")
    print(f"📊 Samples: {len(test_data)}")
    
    try:
        for item in tqdm(test_data, desc="Processing"):
            res = query_ollama(item['image_path'], selected_model, SYSTEM_PROMPT)
            preds.append(clean_json_output(res))
            gts.append(item['gt_data'])
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted! calculating results so far...")

    print(f"\n{Colors.HEADER}--- Step 5: Final Report ---{Colors.END}")
    results = evaluate_metrics(preds, gts)

    print("\n" + "="*45)
    print(f" REPORT: {selected_model}")
    print("="*45)
    for k, v in results.items():
        print(f" {k:<20} : {v}")
    print("="*45)

if __name__ == "__main__":
    main()