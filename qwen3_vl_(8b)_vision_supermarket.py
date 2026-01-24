import os
import sys
import io
import json
import math
import random
import re
import difflib
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageOps
import torch
from datasets import Dataset
from unsloth import FastVisionModel
from unsloth.trainer import UnslothVisionDataCollator
from trl import SFTTrainer, SFTConfig

# Qwen3-VL finetune for supermarket deal extraction (page-level by default).

REPO_DIR = None  # Set to your repo path or leave None to auto-detect
GDRIVE_ZIP_ID = "1uW1Qpd8Z5R1dBrbbWJiXj8G83mazuXq6"
GDRIVE_ZIP_NAME = "smart-deal-finder-main.zip"
AUTO_DOWNLOAD_FROM_GDRIVE = True
DATA_ROOT = "data/images_uniform"
MODEL_ID = "unsloth/Qwen3-VL-8B-Instruct-unsloth-bnb-4bit"
OUTPUT_DIR = "outputs_qwen3_vl"
PREBENCH_SCRIPT = "qwen3_vl_(8b)_vision_supermarket_prebench.py"
RUN_PREBENCH = True
RUN_POSTBENCH = True
PREDICT_WITH_GENERATE = True
EVAL_DEBUG_SAMPLES = 0
BENCH_MAX_SAMPLES = 10
BENCH_MAX_NEW_TOKENS = 512
RUN_GENERATE_EVAL = True
RUN_GENERATE_EVAL_BEFORE = False
GENERATE_EVAL_MAX_SAMPLES = 20
GENERATE_EVAL_MAX_NEW_TOKENS = 512
DIAG_VERBOSE = True
DIAG_MAX_SAMPLES = 3

# Data behavior
USE_PAGE_LEVEL = True  # True: full page -> list of deals; False: crop each bbox -> single deal
BBOX_PAD = 0.02

# Training (use STAGE to select a preset)
STAGE = "val_fast"  # options: val_fast, pilot, dev, train, long
SEED = 3407
MAX_LENGTH = 2048
NUMERIC_TOLERANCE = 0.01
NAME_SIM_THRESHOLD = 0.8
UNIT_SIM_THRESHOLD = 0.5
MIN_NAME_LEN = 4

STAGE_CONFIGS = {
    # fastest validation / smoke check
    "val_fast": {
        "max_samples": 120,
        "val_ratio": 0.1,
        "eval_max_samples": 20,
        "max_steps": 150,
        "batch_size": 2,
        "grad_accum": 4,
        "learning_rate": 2e-4,
        "eval_steps": 30,
    },
    # small pilot run
    "pilot": {
        "max_samples": 200,
        "val_ratio": 0.1,
        "eval_max_samples": 20,
        "max_steps": 200,
        "batch_size": 2,
        "grad_accum": 4,
        "learning_rate": 2e-4,
        "eval_steps": 100,
    },
    # development run
    "dev": {
        "max_samples": 600,
        "val_ratio": 0.1,
        "eval_max_samples": 50,
        "max_steps": 500,
        "batch_size": 2,
        "grad_accum": 4,
        "learning_rate": 2e-4,
        "eval_steps": 200,
    },
    # full training
    "train": {
        "max_samples": None,
        "val_ratio": 0.08,
        "eval_max_samples": 100,
        "max_steps": 1200,
        "batch_size": 2,
        "grad_accum": 4,
        "learning_rate": 2e-4,
        "eval_steps": 300,
    },
    # longer run
    "long": {
        "max_samples": None,
        "val_ratio": 0.05,
        "eval_max_samples": 150,
        "max_steps": 2500,
        "batch_size": 2,
        "grad_accum": 4,
        "learning_rate": 1.5e-4,
        "eval_steps": 500,
    },
}


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def find_repo_dir() -> Path:
    if REPO_DIR:
        candidate = Path(REPO_DIR)
        if candidate.exists():
            return candidate
        raise SystemExit(f"Repo directory '{REPO_DIR}' not found.")

    candidates = [
        Path("/content/smart-deal-finder-main"),
        Path("/content/smart-deal-finder"),
        Path("/content/drive/MyDrive/smart-deal-finder-main"),
        Path("/content/drive/MyDrive/smart-deal-finder"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    for root in (Path("/content"), Path("/content/drive/MyDrive")):
        if not root.exists():
            continue
        for path in root.rglob("data/images_uniform"):
            return path.parent.parent

    raise SystemExit("Repo directory not found. Set REPO_DIR to the existing path.")


def ensure_repo_available() -> Path:
    repo_dir = None
    try:
        repo_dir = find_repo_dir()
        return repo_dir
    except SystemExit:
        if not AUTO_DOWNLOAD_FROM_GDRIVE:
            raise

    print("Repo not found. Downloading from Google Drive...")
    import subprocess as _subprocess
    _subprocess.check_call([sys.executable, "-m", "pip", "-q", "install", "-U", "gdown"])
    _subprocess.check_call(
        ["gdown", "--id", GDRIVE_ZIP_ID, "-O", GDRIVE_ZIP_NAME]
    )
    _subprocess.check_call(["unzip", "-q", GDRIVE_ZIP_NAME])
    return find_repo_dir()


def resolve_image_path(image_dir: Path, stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = image_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def _coerce_image(image: Any) -> Image.Image:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, dict):
        if "image" in image and isinstance(image["image"], Image.Image):
            return image["image"].convert("RGB")
        if "path" in image:
            return Image.open(image["path"]).convert("RGB")
        if "bytes" in image:
            return Image.open(io.BytesIO(image["bytes"])).convert("RGB")
    raise TypeError(f"Unsupported image type for eval: {type(image)}")


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
    if "€" in s or "eur" in s:
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


def run_prebench(
    repo_dir: Path,
    data_root: Path,
    label: str,
    lora_path: Path | None = None,
) -> None:
    print(f"[PREBENCH] Running {label} evaluation...")
    output_dir = repo_dir / OUTPUT_DIR / "prebench_inline"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"prebench_{label.replace(' ', '_')}.jsonl"
    summary_path = output_dir / f"prebench_{label.replace(' ', '_')}_summary.json"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = FastVisionModel.from_pretrained(
        MODEL_ID,
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth",
    )
    if lora_path is not None and lora_path.exists():
        try:
            from peft import PeftModel
            model = PeftModel.from_pretrained(model, str(lora_path))
            print(f"[PREBENCH] Loaded LoRA adapter: {lora_path}")
        except Exception as exc:
            print(f"[WARN] Failed to load LoRA adapter at {lora_path}: {exc}")
    FastVisionModel.for_inference(model)

    samples = build_samples(data_root, BENCH_MAX_SAMPLES)
    if not samples:
        print("[WARN] Prebench: no samples found.")
        return

    agg = {
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
        "avg_pred_tokens": 0.0,
        "empty_pred_rate": 0.0,
        "empty_gt_rate": 0.0,
    }
    json_ok = 0
    empty_pred = 0
    empty_gt = 0
    pred_chars_sum = 0
    pred_tokens_sum = 0
    diag_samples: List[Dict[str, Any]] = []

    with log_path.open("w", encoding="utf-8") as log_f:
        for idx, sample in enumerate(samples, start=1):
            prompt_text = sample["messages"][0]["content"][0]["text"]
            image = _coerce_image(sample["messages"][0]["content"][1]["image"])
            target_text = sample["messages"][1]["content"][0]["text"]

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image", "image": image},
                    ],
                }
            ]
            input_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
            inputs = tokenizer(
                image,
                input_text,
                add_special_tokens=False,
                return_tensors="pt",
            ).to(device)
            input_len = int(inputs["input_ids"].shape[-1])
            with torch.inference_mode():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=BENCH_MAX_NEW_TOKENS,
                    use_cache=True,
                )
            gen_ids = output_ids[0][input_len:]
            pred_text = tokenizer.decode(gen_ids, skip_special_tokens=True)

            label_obj = _parse_json_from_text(target_text)
            pred_obj = _parse_json_from_text(pred_text)
            gt_list = _ensure_list(label_obj)
            pred_list = _ensure_list(pred_obj)
            metrics = _score_prediction_lists(gt_list, pred_list)
            metrics["json_parse_ok"] = pred_obj is not None

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
            pred_tokens_sum += len(gen_ids)
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
            print(
                f"[PREBENCH {idx}/{len(samples)}] "
                f"recall={metrics['deal_retrieval_rate']:.3f} "
                f"precision={metrics['precision']:.3f} "
                f"safe_deal={metrics['safe_deal_rate']:.3f}"
            )

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
        agg["avg_pred_tokens"] = pred_tokens_sum / denom
        agg["empty_pred_rate"] = empty_pred / denom
        agg["empty_gt_rate"] = empty_gt / denom

    with summary_path.open("w", encoding="utf-8") as f:
        payload = {"summary": agg}
        if DIAG_VERBOSE and diag_samples:
            payload["diagnostics"] = diag_samples
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Prebench summary:")
    print(json.dumps(agg, ensure_ascii=False, indent=2))
    if DIAG_VERBOSE and diag_samples:
        print("Prebench diagnostics (samples):")
        print(json.dumps(diag_samples, ensure_ascii=False, indent=2))


def run_generate_eval(
    model,
    tokenizer,
    dataset: Dataset | None,
    label: str,
    output_dir: Path,
    max_samples: int,
    max_new_tokens: int,
) -> None:
    if dataset is None or len(dataset) == 0:
        print(f"[GENEVAL] Skipping {label}: no eval dataset.")
        return

    output_dir = output_dir / "generate_eval"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / f"geneval_{label.replace(' ', '_')}.jsonl"
    summary_path = output_dir / f"geneval_{label.replace(' ', '_')}_summary.json"

    eval_count = min(max_samples, len(dataset))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    FastVisionModel.for_inference(model)

    agg = {
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
        "avg_pred_tokens": 0.0,
        "empty_pred_rate": 0.0,
        "empty_gt_rate": 0.0,
    }
    json_ok = 0
    empty_pred = 0
    empty_gt = 0
    pred_chars_sum = 0
    pred_tokens_sum = 0
    diag_samples: List[Dict[str, Any]] = []

    with log_path.open("w", encoding="utf-8") as log_f:
        for idx in range(eval_count):
            sample = dataset[idx]
            prompt_text = sample["messages"][0]["content"][0]["text"]
            image = _coerce_image(sample["messages"][0]["content"][1]["image"])
            target_text = sample["messages"][1]["content"][0]["text"]

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image", "image": image},
                    ],
                }
            ]
            input_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True)
            inputs = tokenizer(
                image,
                input_text,
                add_special_tokens=False,
                return_tensors="pt",
            ).to(device)
            input_len = int(inputs["input_ids"].shape[-1])
            with torch.inference_mode():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    use_cache=True,
                )
            gen_ids = output_ids[0][input_len:]
            pred_text = tokenizer.decode(gen_ids, skip_special_tokens=True)

            label_obj = _parse_json_from_text(target_text)
            pred_obj = _parse_json_from_text(pred_text)
            gt_list = _ensure_list(label_obj)
            pred_list = _ensure_list(pred_obj)
            metrics = _score_prediction_lists(gt_list, pred_list)
            metrics["json_parse_ok"] = pred_obj is not None

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
            pred_tokens_sum += len(gen_ids)
            if metrics["pred_total"] == 0:
                empty_pred += 1
            if metrics["gt_total"] == 0:
                empty_gt += 1
            if DIAG_VERBOSE and len(diag_samples) < DIAG_MAX_SAMPLES:
                if not metrics["json_parse_ok"] or metrics["pred_total"] == 0:
                    diag_samples.append(
                        {
                            "index": idx + 1,
                            "json_parse_ok": metrics["json_parse_ok"],
                            "gt_total": metrics["gt_total"],
                            "pred_total": metrics["pred_total"],
                            "prediction_head": pred_text[:400],
                            "ground_truth_head": target_text[:400],
                        }
                    )

            log_record = {
                "index": idx + 1,
                "prompt": prompt_text,
                "ground_truth": target_text,
                "prediction": pred_text,
                "metrics": metrics,
            }
            log_f.write(json.dumps(log_record, ensure_ascii=False) + "\n")
            log_f.flush()
            print(
                f"[GENEVAL {idx + 1}/{eval_count}] "
                f"recall={metrics['deal_retrieval_rate']:.3f} "
                f"precision={metrics['precision']:.3f} "
                f"safe_deal={metrics['safe_deal_rate']:.3f}"
            )

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
        agg["avg_pred_tokens"] = pred_tokens_sum / denom
        agg["empty_pred_rate"] = empty_pred / denom
        agg["empty_gt_rate"] = empty_gt / denom

    with summary_path.open("w", encoding="utf-8") as f:
        payload = {"summary": agg}
        if DIAG_VERBOSE and diag_samples:
            payload["diagnostics"] = diag_samples
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Generate eval summary:")
    print(json.dumps(agg, ensure_ascii=False, indent=2))
    if DIAG_VERBOSE and diag_samples:
        print("Generate eval diagnostics (samples):")
        print(json.dumps(diag_samples, ensure_ascii=False, indent=2))

    FastVisionModel.for_training(model)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def crop_with_bbox(image: Image.Image, bbox: List[float], pad: float) -> Image.Image:
    w, h = image.size
    x1, y1, x2, y2 = bbox
    dx = (x2 - x1) * pad
    dy = (y2 - y1) * pad
    x1 = clamp(x1 - dx, 0.0, 1.0)
    y1 = clamp(y1 - dy, 0.0, 1.0)
    x2 = clamp(x2 + dx, 0.0, 1.0)
    y2 = clamp(y2 + dy, 0.0, 1.0)
    left = int(x1 * w)
    top = int(y1 * h)
    right = int(x2 * w)
    bottom = int(y2 * h)
    return image.crop((left, top, right, bottom)).convert("RGB")


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
    if "€" in s or "eur" in s:
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
            "Task: Extract all supermarket deals from this flyer page.\n"
            "Return ONLY valid JSON (no extra text).\n"
            "Schema (JSON array of objects):\n"
            "[\n"
            "  {\n"
            "    \"product_name\": string | null,\n"
            "    \"price\": string | number | null,\n"
            "    \"discount\": string | null,\n"
            "    \"unit\": string | null,\n"
            "    \"original_price\": string | number | null\n"
            "  }\n"
            "]\n"
            "Rules:\n"
            "- Use null if a field is missing.\n"
            "- Keep prices as numbers or numeric strings (e.g., \"1.99\").\n"
            "- Product name should focus on the item, not marketing text.\n"
            "- Unit should be the package/unit only (e.g., \"1-kg-Packung\", \"je Stück\").\n"
            "- Do NOT output legal price-per-unit info (e.g., \"kg-Preis\", \"€/kg\", \"€/l\") as unit.\n"
            "- If multiple deals exist, include all of them."
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
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": instruction},
                                    {"type": "image", "image": page_image},
                                ],
                            },
                            {"role": "assistant", "content": [{"type": "text", "text": target}]},
                        ]
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
                            "messages": [
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": instruction},
                                        {"type": "image", "image": crop},
                                    ],
                                },
                                {"role": "assistant", "content": [{"type": "text", "text": target}]},
                            ]
                        }
                    )
            if max_samples and len(samples) >= max_samples:
                return samples
    return samples


def main() -> None:
    set_seed(SEED)
    repo_dir = ensure_repo_available()
    data_root = repo_dir / DATA_ROOT

    if STAGE not in STAGE_CONFIGS:
        raise SystemExit(f"Unknown STAGE '{STAGE}'. Use one of: {', '.join(STAGE_CONFIGS)}")
    stage = STAGE_CONFIGS[STAGE]

    if RUN_PREBENCH:
        run_prebench(repo_dir, data_root, "before training")

    samples = build_samples(data_root, stage["max_samples"])
    if not samples:
        raise SystemExit("No samples found. Check data paths.")

    dataset = Dataset.from_list(samples)
    print(
        f"Loaded samples: {len(dataset)} | "
        f"page_level={USE_PAGE_LEVEL} | "
        f"stage={STAGE}"
    )
    print(f"Stage config: {stage}")
    if 0.0 < stage["val_ratio"] < 1.0:
        split = dataset.train_test_split(test_size=stage["val_ratio"], seed=SEED)
        train_dataset = split["train"]
        eval_dataset = split["test"]
        if stage["eval_max_samples"]:
            eval_dataset = eval_dataset.select(
                range(min(stage["eval_max_samples"], len(eval_dataset)))
            )
    else:
        train_dataset = dataset
        eval_dataset = None
    print(
        f"Train size: {len(train_dataset)} | "
        f"Eval size: {len(eval_dataset) if eval_dataset is not None else 0}"
    )
    if eval_dataset is not None and len(eval_dataset) < 20:
        print(f"[WARN] Eval set is small ({len(eval_dataset)}). Metrics may be noisy.")

    model, tokenizer = FastVisionModel.from_pretrained(
        MODEL_ID,
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth",
    )
    print(f"Model: {MODEL_ID}")
    if PREDICT_WITH_GENERATE:
        print("[WARN] Trainer eval metrics are disabled; using generate-based eval instead.")

    model = FastVisionModel.get_peft_model(
        model,
        finetune_vision_layers=True,
        finetune_language_layers=True,
        finetune_attention_modules=True,
        finetune_mlp_modules=True,
        r=16,
        lora_alpha=16,
        lora_dropout=0,
        bias="none",
        random_state=SEED,
        use_rslora=False,
        loftq_config=None,
    )

    FastVisionModel.for_training(model)
    if len(train_dataset) > 0:
        sample_preview = train_dataset[0]["messages"][0]["content"][0]["text"]
        target_preview = train_dataset[0]["messages"][1]["content"][0]["text"]
        print("Prompt preview:")
        print(sample_preview[:600])
        print("Target preview:")
        print(target_preview[:600])
    if RUN_GENERATE_EVAL and RUN_GENERATE_EVAL_BEFORE:
        run_generate_eval(
            model,
            tokenizer,
            eval_dataset,
            "before training",
            repo_dir / OUTPUT_DIR,
            GENERATE_EVAL_MAX_SAMPLES,
            GENERATE_EVAL_MAX_NEW_TOKENS,
        )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        if isinstance(logits, (tuple, list)):
            logits = logits[0]
        if isinstance(labels, (tuple, list)):
            labels = labels[0]
        if torch.is_tensor(logits):
            logits = logits.detach().cpu().numpy()
        if torch.is_tensor(labels):
            labels = labels.detach().cpu().numpy()
        preds = logits
        results = {
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
        }
        total = 0
        json_ok = 0
        deal_retrieved = 0
        price_correct = 0
        unit_correct = 0
        e2e_correct = 0
        matched_count = 0
        pred_total_sum = 0
        gt_total_sum = 0

        is_logits = hasattr(preds, "ndim") and preds.ndim == 3
        for idx, (pred_ids, label_ids) in enumerate(zip(preds, labels)):
            label_mask = label_ids != -100
            label_tokens = [int(t) for t in label_ids[label_mask]]
            label_text_raw = tokenizer.decode(label_tokens, skip_special_tokens=True)
            if is_logits:
                pred_ids = pred_ids.argmax(axis=-1)
                pred_tokens = [int(t) for t in pred_ids[label_mask]]
            else:
                pred_tokens = [int(t) for t in pred_ids if t != -100]
            pred_text_raw = tokenizer.decode(pred_tokens, skip_special_tokens=True)
            total += 1

            label_obj = _parse_json_from_text(label_text_raw)
            pred_obj = _parse_json_from_text(pred_text_raw)
            if pred_obj is not None:
                json_ok += 1

            gt_list = _ensure_list(label_obj)
            pred_list = _ensure_list(pred_obj)
            metrics = _score_prediction_lists(gt_list, pred_list)

            gt_total_sum += metrics["gt_total"]
            matched_count += metrics["matched_count"]
            deal_retrieved += metrics["matched_count"]
            pred_total_sum += metrics["pred_total"]
            price_correct += metrics["price_correct_count"]
            unit_correct += metrics["unit_correct_count"]
            e2e_correct += metrics["e2e_correct_count"]
            if EVAL_DEBUG_SAMPLES and idx < EVAL_DEBUG_SAMPLES:
                print(f"[EVAL DEBUG {idx}] label_text={label_text_raw[:400]}")
                print(f"[EVAL DEBUG {idx}] pred_text={pred_text_raw[:400]}")

        if total > 0:
            precision = matched_count / pred_total_sum if pred_total_sum else 0.0
            recall = deal_retrieved / gt_total_sum if gt_total_sum else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            results["json_parse_rate"] = json_ok / total
            results["deal_retrieval_rate"] = deal_retrieved / gt_total_sum if gt_total_sum else 0.0
            results["precision"] = precision
            results["f1"] = f1
            results["overprediction_rate"] = (pred_total_sum - matched_count) / pred_total_sum if pred_total_sum else 0.0
            results["price_reliability"] = price_correct / matched_count if matched_count else 0.0
            results["safe_deal_rate"] = e2e_correct / gt_total_sum if gt_total_sum else 0.0
            results["end_to_end_recall"] = e2e_correct / gt_total_sum if gt_total_sum else 0.0
            results["name_accuracy"] = deal_retrieved / gt_total_sum if gt_total_sum else 0.0
            results["price_accuracy"] = price_correct / gt_total_sum if gt_total_sum else 0.0
            results["unit_accuracy"] = unit_correct / gt_total_sum if gt_total_sum else 0.0
        return results

    config_kwargs = dict(
        per_device_train_batch_size=stage["batch_size"],
        gradient_accumulation_steps=stage["grad_accum"],
        warmup_steps=5,
        max_steps=stage["max_steps"],
        learning_rate=stage["learning_rate"],
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.001,
        lr_scheduler_type="linear",
        seed=SEED,
        output_dir=str(repo_dir / OUTPUT_DIR),
        report_to="none",
        remove_unused_columns=False,
        dataset_text_field="",
        dataset_kwargs={"skip_prepare_dataset": True},
        max_length=MAX_LENGTH,
    )
    if eval_dataset is not None and not PREDICT_WITH_GENERATE:
        config_kwargs["eval_strategy"] = "steps"
        config_kwargs["eval_steps"] = stage["eval_steps"]
    else:
        config_kwargs["eval_strategy"] = "no"

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        data_collator=UnslothVisionDataCollator(model, tokenizer),
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics if (eval_dataset is not None and not PREDICT_WITH_GENERATE) else None,
        args=SFTConfig(**config_kwargs),
    )

    trainer.train()

    if RUN_GENERATE_EVAL:
        run_generate_eval(
            model,
            tokenizer,
            eval_dataset,
            "after training",
            repo_dir / OUTPUT_DIR,
            GENERATE_EVAL_MAX_SAMPLES,
            GENERATE_EVAL_MAX_NEW_TOKENS,
        )

    model.save_pretrained(str(repo_dir / "lora_model_qwen3_vl"))
    tokenizer.save_pretrained(str(repo_dir / "lora_model_qwen3_vl"))

    if RUN_POSTBENCH:
        lora_path = repo_dir / "lora_model_qwen3_vl"
        run_prebench(repo_dir, data_root, "after training", lora_path)


if __name__ == "__main__":
    main()
