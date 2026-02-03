from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import random
import re
import difflib
import sys
import time
import urllib.request
import urllib.error
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ollama prebench for end-to-end JSON extraction (vision -> JSON).

DATA_ROOT = "data/images_uniform"
OUTPUT_DIR = "outputs_ollama_prebench"
USE_PAGE_LEVEL = True
BBOX_PAD = 0.02
SEED = 3407
NUMERIC_TOLERANCE = 0.01
NAME_SIM_THRESHOLD = 0.8
UNIT_SIM_THRESHOLD = 0.5
MIN_NAME_LEN = 4
MAX_SAMPLES = 20
DIAG_VERBOSE = True
DIAG_MAX_SAMPLES = 3

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_TIMEOUT_SEC = 600

Image = None


@dataclass
class ModelSpec:
    model_id: str
    options: Dict[str, Any] = field(default_factory=dict)


MODEL_SPECS = [
    ModelSpec("qwen2.5vl:7b"),
    ModelSpec("ministral-3:8b"),
    ModelSpec("qwen3-vl:8b"),
    ModelSpec("gemma3:4b"),
    ModelSpec("qwen2.5vl:3b"),
    ModelSpec("qwen3-vl:4b"),
    ModelSpec("ministral-3:3b"),
    ModelSpec("gemma3:1b"),
    ModelSpec("gemma3:270m"),
    ModelSpec("qwen3-vl:2b"),
]


def _ensure_runtime() -> None:
    global Image
    if Image is not None:
        return
    try:
        from PIL import Image as _Image
    except Exception:
        print("[ERROR] Missing runtime dependency: pillow")
        raise
    Image = _Image


def set_seed(seed: int) -> None:
    random.seed(seed)


def resolve_image_path(image_dir: Path, stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = image_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def _normalize_text(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", ".")
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except Exception:
                return None
    return None


def _normalize_price(value: Any) -> str | None:
    num = _parse_number(value)
    if num is None:
        return None
    return f"{num:.2f}"


def _normalize_discount(value: Any) -> str | None:
    if value is None:
        return None
    s = _normalize_text(value)
    if not s:
        return None
    if re.search(r"\d", s) is None:
        return s
    num = _parse_number(s)
    if num is None:
        return s
    if "%" in s:
        return f"{num:.0f}%"
    return s


def _normalize_unit(value: Any) -> str | None:
    s = _normalize_text(value).lower()
    if not s:
        return None
    if re.fullmatch(r"[0-9]+([.,][0-9]+)?", s):
        return None
    if "eur" in s or "€" in s:
        return None
    s = re.sub(r"(kg[- ]?preis|price per kg|preis/kg|€/kg|eur/kg|/kg)\s*[-:]?\s*[0-9]+([.,][0-9]+)?", "", s)
    s = re.sub(r"(l[- ]?preis|price per l|preis/l|€/l|eur/l|/l)\s*[-:]?\s*[0-9]+([.,][0-9]+)?", "", s)
    s = s.replace("stück", "stk").replace("stueck", "stk").replace("stuck", "stk").replace("piece", "stk")
    s = s.replace("packung", "pack").replace("pk", "pack")
    s = s.replace("liter", "l").replace("milliliter", "ml").replace("gramm", "g")
    s = s.replace("kilogramm", "kg")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "product_name": _normalize_text(entry.get("product_name")) or None,
        "price": _normalize_price(entry.get("price")),
        "discount": _normalize_discount(entry.get("discount")),
        "unit": _normalize_unit(entry.get("unit")),
        "original_price": _normalize_price(entry.get("original_price")),
    }


def build_samples(data_root: Path, max_samples: int | None) -> List[Dict[str, Any]]:
    if USE_PAGE_LEVEL:
        instruction = (
            "Analyze this German supermarket brochure page and extract ALL product deals.\n"
            "\n"
            "For EACH product you see, extract:\n"
            "- product_name: Full product name (in German)\n"
            "- price: Current price (number only, e.g., \"2.99\")\n"
            "- original_price: Original price if shown (number only)\n"
            "- discount: Discount percentage or amount if shown\n"
            "- unit: Package size/weight (e.g., \"500 g\", \"1 L\")\n"
            "- brand: Brand name if visible\n"
            "\n"
            "Return ONLY a valid JSON array with all products. Example format:\n"
            "[\n"
            "  {\n"
            "    \"product_name\": \"Coca-Cola\",\n"
            "    \"price\": \"1.99\",\n"
            "    \"unit\": \"1.5 L\",\n"
            "    \"brand\": \"Coca-Cola\"\n"
            "  },\n"
            "  {\n"
            "    \"product_name\": \"Nutella\",\n"
            "    \"price\": \"3.49\",\n"
            "    \"original_price\": \"4.99\",\n"
            "    \"discount\": \"30%\",\n"
            "    \"unit\": \"450 g\",\n"
            "    \"brand\": \"Ferrero\"\n"
            "  }\n"
            "]\n"
            "\n"
            "Extract ALL products visible on the page. Return ONLY the JSON array, no other text."
        )
    else:
        instruction = (
            "Task: Extract the product deal.\n"
            "Return ONLY valid JSON (no extra text).\n"
            "Schema:\n"
            "{\n"
            "  \"product_name\": string | null,\n"
            "  \"price\": string | number | null,\n"
            "  \"discount\": string | null,\n"
            "  \"unit\": string | null,\n"
            "  \"original_price\": string | number | null\n"
            "}\n"
            "Rules:\n"
            "- Use null if a field is missing.\n"
            "- Keep prices as numbers or numeric strings (e.g., \"1.99\").\n"
            "- Product name should focus on the item, not marketing text.\n"
            "- Unit should be the package/unit only (e.g., \"1-kg-Packung\", \"je Stück\").\n"
            "- Do NOT output legal price-per-unit info (e.g., \"kg-Preis\", \"€/kg\", \"€/l\") as unit."
        )

    samples: List[Dict[str, Any]] = []
    annotated_dirs = sorted([p for p in data_root.iterdir() if p.is_dir() and p.name.endswith("_annotated")])
    for ann_dir in annotated_dirs:
        image_dir = ann_dir.with_name(ann_dir.name.replace("_annotated", ""))
        if not image_dir.exists():
            continue
        for json_path in sorted(ann_dir.glob("*.json")):
            image_path = resolve_image_path(image_dir, json_path.stem)
            if image_path is None:
                continue
            try:
                with json_path.open("r", encoding="utf-8") as f:
                    entries = json.load(f)
            except json.JSONDecodeError:
                continue
            if not entries or not isinstance(entries, list):
                continue

            page_image = Image.open(image_path).convert("RGB")

            if USE_PAGE_LEVEL:
                cleaned = [clean_entry(e) for e in entries]
                target = json.dumps(cleaned, ensure_ascii=False)
                samples.append(
                    {
                        "prompt": instruction,
                        "image": page_image,
                        "target": target,
                    }
                )
            else:
                for entry in entries:
                    bbox = entry.get("bbox")
                    if not bbox or len(bbox) != 4:
                        continue
                    crop = crop_with_bbox(page_image, bbox, BBOX_PAD)
                    target = json.dumps(clean_entry(entry), ensure_ascii=False)
                    samples.append(
                        {
                            "prompt": instruction,
                            "image": crop,
                            "target": target,
                        }
                    )
            if max_samples and len(samples) >= max_samples:
                return samples
    return samples


def _parse_json_from_text(text: str) -> Any | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    candidates: List[str] = []
    for m in re.finditer(r"\[.*?\]", text, flags=re.DOTALL):
        candidates.append(m.group(0))
    for m in re.finditer(r"\{.*?\}", text, flags=re.DOTALL):
        candidates.append(m.group(0))
    for cand in reversed(candidates):
        try:
            return json.loads(cand)
        except Exception:
            continue
    return None


def _normalize_eval_text(text: Any) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _token_set_similarity(a: str, b: str) -> float:
    tokens_a = set(re.findall(r"[a-z0-9]+", a.lower()))
    tokens_b = set(re.findall(r"[a-z0-9]+", b.lower()))
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _name_similarity(a: str, b: str) -> float:
    norm_a = _normalize_eval_text(a)
    norm_b = _normalize_eval_text(b)
    seq = difflib.SequenceMatcher(None, norm_a, norm_b).ratio()
    tok = _token_set_similarity(norm_a, norm_b)
    sub = 0.0
    if len(norm_a) >= MIN_NAME_LEN and len(norm_b) >= MIN_NAME_LEN:
        if norm_a in norm_b or norm_b in norm_a:
            sub = 0.9
    return max(seq, tok, sub)


def _normalize_unit_eval(text: Any) -> str:
    s = _normalize_eval_text(text)
    if not s:
        return ""
    if re.fullmatch(r"[0-9]+([.,][0-9]+)?", s):
        return ""
    if "eur" in s or "€" in s:
        return ""
    s = re.sub(r"(kg[- ]?preis|price per kg|preis/kg|€/kg|eur/kg|/kg)\s*[-:]?\s*[0-9]+([.,][0-9]+)?", "", s)
    s = re.sub(r"(l[- ]?preis|price per l|preis/l|€/l|eur/l|/l)\s*[-:]?\s*[0-9]+([.,][0-9]+)?", "", s)
    s = s.replace("stück", "stk").replace("stueck", "stk").replace("stuck", "stk").replace("piece", "stk")
    s = s.replace("packung", "pack").replace("pk", "pack")
    s = s.replace("liter", "l").replace("milliliter", "ml").replace("gramm", "g")
    s = s.replace("kilogramm", "kg")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _ensure_list(obj: Any) -> List[Dict[str, Any]]:
    if isinstance(obj, list):
        return [o for o in obj if isinstance(o, dict)]
    if isinstance(obj, dict):
        return [obj]
    return []


def _match_deals(
    gt_list: List[Dict[str, Any]],
    pred_list: List[Dict[str, Any]],
) -> List[Tuple[int, int, float]]:
    matches: List[Tuple[int, int, float]] = []
    used_pred = set()
    for gi, gt in enumerate(gt_list):
        gt_name = gt.get("product_name")
        best = (-1, 0.0)
        for pi, pred in enumerate(pred_list):
            if pi in used_pred:
                continue
            sim = _name_similarity(gt_name, pred.get("product_name"))
            if sim > best[1]:
                best = (pi, sim)
        if best[0] != -1 and best[1] >= NAME_SIM_THRESHOLD:
            used_pred.add(best[0])
            matches.append((gi, best[0], best[1]))
    return matches


def _score_prediction_lists(
    gt_list: List[Dict[str, Any]],
    pred_list: List[Dict[str, Any]],
) -> Dict[str, float]:
    matches = _match_deals(gt_list, pred_list)
    matched_count = len(matches)
    pred_total = len(pred_list)
    gt_total = len(gt_list)
    price_correct = 0
    unit_correct = 0
    e2e_correct = 0

    for gi, pi, _ in matches:
        gt = gt_list[gi]
        pred = pred_list[pi]

        gt_price = _parse_number(gt.get("price"))
        pred_price = _parse_number(pred.get("price"))
        price_ok = (
            gt_price is not None
            and pred_price is not None
            and abs(gt_price - pred_price) <= NUMERIC_TOLERANCE
        )
        if price_ok:
            price_correct += 1

        gt_unit = _normalize_unit_eval(gt.get("unit"))
        pred_unit = _normalize_unit_eval(pred.get("unit"))
        if not gt_unit or not pred_unit:
            unit_ok = True
        else:
            unit_ok = _token_set_similarity(gt_unit, pred_unit) >= UNIT_SIM_THRESHOLD
        if unit_ok:
            unit_correct += 1

        if price_ok and unit_ok:
            e2e_correct += 1

    precision = matched_count / pred_total if pred_total else 0.0
    recall = matched_count / gt_total if gt_total else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "gt_total": gt_total,
        "pred_total": pred_total,
        "matched_count": matched_count,
        "price_correct_count": price_correct,
        "unit_correct_count": unit_correct,
        "e2e_correct_count": e2e_correct,
        "deal_retrieval_rate": recall,
        "precision": precision,
        "f1": f1,
        "overprediction_rate": (pred_total - matched_count) / pred_total if pred_total else 0.0,
        "price_reliability": price_correct / matched_count if matched_count else 0.0,
        "safe_deal_rate": e2e_correct / gt_total if gt_total else 0.0,
        "end_to_end_recall": e2e_correct / gt_total if gt_total else 0.0,
        "name_accuracy": recall,
        "price_accuracy": price_correct / gt_total if gt_total else 0.0,
        "unit_accuracy": unit_correct / gt_total if gt_total else 0.0,
    }


def crop_with_bbox(image: Image.Image, bbox: List[float], pad: float) -> Image.Image:
    w, h = image.size
    x1, y1, x2, y2 = bbox
    dx = (x2 - x1) * pad
    dy = (y2 - y1) * pad
    x1 = max(0.0, min(1.0, x1 - dx))
    y1 = max(0.0, min(1.0, y1 - dy))
    x2 = max(0.0, min(1.0, x2 + dx))
    y2 = max(0.0, min(1.0, y2 + dy))
    left = int(x1 * w)
    top = int(y1 * h)
    right = int(x2 * w)
    bottom = int(y2 * h)
    return image.crop((left, top, right, bottom)).convert("RGB")


def _ollama_generate(
    model_id: str,
    prompt: str,
    image: Image.Image,
    options: Dict[str, Any] | None = None,
) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    payload = {
        "model": model_id,
        "prompt": prompt,
        "images": [img_b64],
        "stream": False,
    }
    if options:
        payload["options"] = options
    # Run request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SEC) as response:
            result = json.loads(response.read().decode("utf-8"))
            content = result.get("response", "")
            if not content:
                 print(f"[OLLAMA] WARNING: Empty response from model {model_id}")
                 print(f"[OLLAMA] Raw result: {result}")
            # print(f"[DEBUG] Raw output for {model_id}: {content[:200]}...") # Uncomment to see raw
            return content
    except Exception as e:
        print(f"[OLLAMA] Error running {model_id}: {e}")
        return ""


def _gemini_generate(
    model_id: str,
    prompt: str,
    image: Image.Image,
    api_key: str,
) -> str:
    # Handle model mapping or fallback
    # User asked for 2.5-flash, but API usually expects standard names.
    # We'll try the exact ID, but if it's "gemini-2.5-flash", we might strictly check 
    # if it's mapped to a real endpoint or just pass it through.
    # Google API requires "models/" prefix usually or just the name. 
    # e.g. "gemini-1.5-flash"
    
    real_model = model_id
    if not real_model.startswith("models/") and not real_model.startswith("gemini"):
        real_model = f"models/{real_model}"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{real_model}:generateContent?key={api_key}"
    
    buf = io.BytesIO()
    image.save(buf, format="JPEG") # Gemini prefers JPEG usually or PNG
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt + "\nReturn valid JSON only."},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_b64
                    }
                }
            ]
        }]
    }
    
    # Models like 'flash-image' don't support response_mime_type: application/json
    if "image" not in real_model.lower():
         payload["generationConfig"] = {
            "response_mime_type": "application/json"
        }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    # Rate Limiting & Retry Logic for Gemini
    # User requested approx 9 RPM -> ~6.7s delay. Safety margin: 7s.
    # Also retry on 429/400 errors.
    
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            # Enforce rate limit delay before request (or after, but before is safer for loops)
            # Only needed for 2.0-flash-exp really, but won't hurt others to be safe if specific model
            # Added "pro" to capture 2.5-pro which likely has lower QPM than flash
            if "flash-exp" in real_model or "gemini-3" in real_model or "gemini-2.0" in real_model or "pro" in real_model:
                 time.sleep(7.0) 

            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
            # Parse Gemini response structure
            # { "candidates": [ { "content": { "parts": [ { "text": "..." } ] } } ] }
            try:
                return obj["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                return ""
        
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code == 503: # Rate limit or Service Unavailable
                print(f"[GEMINI] Rate limit hit ({e.code}). Waiting 60s before retry {attempt+1}/{max_retries}...")
                time.sleep(61)
                continue
            elif e.code == 400:
                # Sometimes quota/key errors show as 400. Read body.
                try:
                    err_msg = e.read().decode("utf-8")
                except:
                    err_msg = str(e)
                
                # If it mentions quota or rate limit in text (even if 400), retry
                if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                     print(f"[GEMINI] Quota error (400). Waiting 60s before retry {attempt+1}/{max_retries}...")
                     print(f"Details: {err_msg[:200]}")
                     time.sleep(61)
                     continue
                
                print(f"[GEMINI] HTTP Error {e.code}: {e.reason}")
                print(err_msg)
                return ""
            else:
                print(f"[GEMINI] HTTP Error {e.code}: {e.reason}")
                return ""
        except Exception as e:
            print(f"[GEMINI] Error: {e}")
            return ""
            
    return ""


def _siliconflow_generate(
    model_id: str,
    prompt: str,
    image: Image.Image,
    api_key: str,
) -> str:
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{img_b64}"
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt + "\nReturn valid JSON only."},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
        # "temperature": 0.0, # Removed to avoid 400 error on GLM-Thinking
        "max_tokens": 1024, # Reduced from 4096 to fit in 4k context (img ~2.2k + 1k = 3.2k < 4k)
        # "response_format": {"type": "json_object"} # Caused 400 for GLM
    }

    # Only add response_format for models we know support it (like deepseek maybe? actually deepseek worked with it?)
    # DeepSeek worked with it, but GLM failed. 
    # Let's simple remove it for GLM or generic catch
    if "glm" not in model_id.lower() and "thudm" not in model_id.lower() and "qwen/qwen2" not in model_id.lower():
         payload["response_format"] = {"type": "json_object"}
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST",
    )
    
    # Simple retry logic
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                raw = resp.read().decode("utf-8")
            obj = json.loads(raw)
            # OpenAI format: choices[0].message.content
            try:
                content = obj["choices"][0]["message"]["content"]
                return content
            except (KeyError, IndexError):
                return ""
        except urllib.error.HTTPError as e:
            print(f"[SILICON] HTTP Error {e.code}: {e.reason}")
            try:
                print(e.read().decode("utf-8"))
            except:
                pass
            if e.code == 429:
                time.sleep(10)
                continue
            return ""
        except Exception as e:
            print(f"[SILICON] Error: {e}")
            return ""
    return ""


def _run_model(
    spec: ModelSpec,
    samples: List[Dict[str, Any]],
    output_dir: Path,
    gemini_key: str | None = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    agg = {
        "model_id": spec.model_id,
        "total_samples": 0,
        "json_parse_rate": 0.0,
        "deal_retrieval_rate": 0.0,
        "precision": 0.0,
        "f1": 0.0,
        "overprediction_rate": 0.0,
        "price_reliability": 0.0,
        "safe_deal_rate": 0.0,
        "end_to_end_recall": 0.0,
        "name_accuracy": 0.0,
        "price_accuracy": 0.0,
        "unit_accuracy": 0.0,
        "avg_gt_deals": 0.0,
        "avg_pred_deals": 0.0,
        "avg_pred_chars": 0.0,
        "empty_pred_rate": 0.0,
        "empty_gt_rate": 0.0,
        "bad_image_rate": 0.0,
        "skipped_bad_images": 0,
    }
    json_ok = 0
    empty_pred = 0
    empty_gt = 0
    bad_image = 0
    pred_chars_sum = 0
    diag_samples: List[Dict[str, Any]] = []

    log_path = output_dir / f"{spec.model_id.replace(':', '__').replace('/', '__')}.jsonl"
    with log_path.open("w", encoding="utf-8") as log_f:
        for idx, sample in enumerate(samples, start=1):
            s_start = time.time()
            print(f"  [Sample {idx}/{len(samples)}] Processing...")
            prompt_text = sample["prompt"]
            image = sample["image"]
            target_text = sample["target"]
            if image is None:
                bad_image += 1
                if DIAG_VERBOSE and len(diag_samples) < DIAG_MAX_SAMPLES:
                    diag_samples.append(
                        {
                            "index": idx,
                            "reason": "bad_image",
                            "prompt_head": prompt_text[:200],
                        }
                    )
                log_f.write(
                    json.dumps(
                        {
                            "index": idx,
                            "error": "bad_image",
                            "prompt_head": prompt_text[:200],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                log_f.flush()
                continue

                if not gemini_key:
                    raise ValueError("Gemini API key not provided but model is gemini")
                pred_text = _gemini_generate(spec.model_id, prompt_text, image, gemini_key)
            elif ("deepseek" in spec.model_id.lower() or "glm" in spec.model_id.lower() or "thudm" in spec.model_id.lower() or "qwen" in spec.model_id.lower()) and "ollama" not in spec.model_id.lower() and "/" in spec.model_id:
                # Assume SiliconFlow/Cloud if it's deepseek/glm/qwen AND has a slash (Owner/Model) AND not ollama explicit
                if gemini_key: # We reuse this arg as a generic api_key
                     pred_text = _siliconflow_generate(spec.model_id, prompt_text, image, gemini_key)
                else:
                    # Fallback to Ollama if no key provided
                    pred_text = _ollama_generate(spec.model_id, prompt_text, image, spec.options)
            else:
                pred_text = _ollama_generate(spec.model_id, prompt_text, image, spec.options)
            
            label_obj = _parse_json_from_text(target_text)
            pred_obj = _parse_json_from_text(pred_text)
            
            # DEBUG: If we found 0 deals but the model returned text, maybe our parsing failed?
            pred_list_for_debug = _ensure_list(pred_obj)
            if len(pred_list_for_debug) == 0 and len(pred_text.strip()) > 50:
                 print(f"[DEBUG] Model returned {len(pred_text)} chars but parsed 0 deals. Raw preview:\n{pred_text[:500]}")
            
            gt_list = _ensure_list(label_obj)
            pred_list = _ensure_list(pred_obj)
            metrics = _score_prediction_lists(gt_list, pred_list)
            metrics["json_parse_ok"] = pred_obj is not None
            
            s_elapsed = time.time() - s_start
            print(f"    -> Results: Found {metrics['matched_count']}/{metrics['gt_total']} deals (Pred: {metrics['pred_total']})")
            print(f"    -> Metrics: Recall {metrics['deal_retrieval_rate']:.1%}, Prec {metrics['precision']:.1%}, Time {s_elapsed:.1f}s")

            agg["total_samples"] += 1
            if metrics["json_parse_ok"]:
                json_ok += 1
            agg["deal_retrieval_rate"] += metrics["deal_retrieval_rate"]
            agg["precision"] += metrics["precision"]
            agg["f1"] += metrics["f1"]
            agg["overprediction_rate"] += metrics["overprediction_rate"]
            agg["price_reliability"] += metrics["price_reliability"]
            agg["safe_deal_rate"] += metrics["safe_deal_rate"]
            agg["end_to_end_recall"] += metrics["end_to_end_recall"]
            agg["name_accuracy"] += metrics["name_accuracy"]
            agg["price_accuracy"] += metrics["price_accuracy"]
            agg["unit_accuracy"] += metrics["unit_accuracy"]
            agg["avg_gt_deals"] += metrics["gt_total"]
            agg["avg_pred_deals"] += metrics["pred_total"]
            pred_chars_sum += len(pred_text)
            if metrics["pred_total"] == 0:
                empty_pred += 1
            if metrics["gt_total"] == 0:
                empty_gt += 1
            if DIAG_VERBOSE and len(diag_samples) < DIAG_MAX_SAMPLES:
                if not metrics["json_parse_ok"] or metrics["pred_total"] == 0:
                    diag_samples.append(
                        {
                            "index": idx,
                            "json_parse_ok": metrics["json_parse_ok"],
                            "gt_total": metrics["gt_total"],
                            "pred_total": metrics["pred_total"],
                            "prediction_head": pred_text[:400],
                            "ground_truth_head": target_text[:400],
                        }
                    )

            log_record = {
                "index": idx,
                "prompt": prompt_text,
                "ground_truth": target_text,
                "prediction": pred_text,
                "metrics": metrics,
            }
            log_f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
            log_f.flush()

    if agg["total_samples"] > 0:
        denom = agg["total_samples"]
        agg["json_parse_rate"] = json_ok / denom
        agg["deal_retrieval_rate"] /= denom
        agg["precision"] /= denom
        agg["f1"] /= denom
        agg["overprediction_rate"] /= denom
        agg["price_reliability"] /= denom
        agg["safe_deal_rate"] /= denom
        agg["end_to_end_recall"] /= denom
        agg["name_accuracy"] /= denom
        agg["price_accuracy"] /= denom
        agg["unit_accuracy"] /= denom
        agg["avg_gt_deals"] /= denom
        agg["avg_pred_deals"] /= denom
        agg["avg_pred_chars"] = pred_chars_sum / denom
        agg["empty_pred_rate"] = empty_pred / denom
        agg["empty_gt_rate"] = empty_gt / denom
    if agg["total_samples"] + bad_image:
        agg["skipped_bad_images"] = bad_image
        agg["bad_image_rate"] = bad_image / (agg["total_samples"] + bad_image)

    return agg, diag_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ollama VLM prebench.")
    parser.add_argument("--data-root", default=DATA_ROOT)
    parser.add_argument("--max-samples", type=int, default=MAX_SAMPLES)
    parser.add_argument("--page-level", action="store_true", default=USE_PAGE_LEVEL)
    parser.add_argument("--crop-level", action="store_true", default=False)
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--models", default="")
    parser.add_argument("--timeout-sec", type=int, default=OLLAMA_TIMEOUT_SEC)
    parser.add_argument("--api-key", default=os.environ.get("GEMINI_API_KEY", ""))
    args, _ = parser.parse_known_args()
    return args


def main() -> None:
    args = parse_args()
    _ensure_runtime()
    set_seed(SEED)
    global USE_PAGE_LEVEL, OLLAMA_TIMEOUT_SEC
    OLLAMA_TIMEOUT_SEC = args.timeout_sec
    if args.crop_level:
        USE_PAGE_LEVEL = False
    elif args.page_level:
        USE_PAGE_LEVEL = True

    data_root = Path(args.data_root)
    if not data_root.exists():
        raise SystemExit(f"Data root not found: {data_root}")
    print(f"[OLLAMA] Data root: {data_root}")
    samples = build_samples(data_root, args.max_samples)
    print(f"[OLLAMA] Built {len(samples)} samples.")
    if not samples:
        raise SystemExit("No samples found. Check data paths.")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "summary.csv"
    summary_json = output_dir / "summary.json"

    specs = MODEL_SPECS
    if args.models.strip():
        ids = [m.strip() for m in args.models.split(",") if m.strip()]
        specs = [ModelSpec(m) for m in ids]

    all_summaries: List[Dict[str, Any]] = []
    diagnostics: Dict[str, Any] = {}
    for spec in specs:
        print(f"[OLLAMA] Running {spec.model_id}")
        start = time.time()
        try:
            summary, diag = _run_model(spec, samples, output_dir, gemini_key=args.api_key)
        except Exception as exc:
            summary = {"model_id": spec.model_id, "error": str(exc)}
            diag = [{"error": str(exc)}]
        summary["elapsed_sec"] = time.time() - start
        all_summaries.append(summary)
        if DIAG_VERBOSE and diag:
            diagnostics[spec.model_id] = diag

        # Save progress after each model
        with summary_json.open("w", encoding="utf-8") as f:
            payload = {"summaries": all_summaries}
            if DIAG_VERBOSE and diagnostics:
                payload["diagnostics"] = diagnostics
            json.dump(payload, f, ensure_ascii=False, indent=2)

        fieldnames = sorted({k for s in all_summaries for k in s.keys()})
        with summary_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in all_summaries:
                writer.writerow(row)
        
        print(f"[OLLAMA] Updated {summary_json} and {summary_csv}")


if __name__ == "__main__":
    main()

