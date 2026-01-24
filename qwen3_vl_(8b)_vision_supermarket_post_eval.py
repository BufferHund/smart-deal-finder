import argparse
import io
import json
import random
import re
import difflib
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image
import torch
from datasets import Dataset
from unsloth import FastVisionModel

# Standalone generate-based evaluation for a trained LoRA adapter.

DATA_ROOT = "data/images_uniform"
MODEL_ID = "unsloth/Qwen3-VL-8B-Instruct-unsloth-bnb-4bit"
OUTPUT_DIR = "outputs_qwen3_vl"
DEFAULT_LORA_DIR = "lora_model_qwen3_vl"
USE_PAGE_LEVEL = True
BBOX_PAD = 0.02
SEED = 3407
NUMERIC_TOLERANCE = 0.01
NAME_SIM_THRESHOLD = 0.8
UNIT_SIM_THRESHOLD = 0.5
MIN_NAME_LEN = 4
DIAG_VERBOSE = True
DIAG_MAX_SAMPLES = 5


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def resolve_image_path(image_dir: Path, stem: str) -> Path | None:
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = image_dir / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def _coerce_image(image: Any) -> Image.Image | None:
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, dict):
        if "image" in image and isinstance(image["image"], Image.Image):
            return image["image"].convert("RGB")
        if "path" in image and image["path"]:
            return Image.open(image["path"]).convert("RGB")
        if "bytes" in image and image["bytes"]:
            return Image.open(io.BytesIO(image["bytes"])).convert("RGB")
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


def run_eval(
    repo_dir: Path,
    data_root: Path,
    lora_path: Path,
    max_samples: int,
    max_new_tokens: int,
) -> None:
    output_dir = repo_dir / OUTPUT_DIR / "post_eval"
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "post_eval.jsonl"
    summary_path = output_dir / "post_eval_summary.json"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, tokenizer = FastVisionModel.from_pretrained(
        MODEL_ID,
        load_in_4bit=True,
        use_gradient_checkpointing="unsloth",
    )
    if lora_path.exists():
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(lora_path))
        print(f"[POST_EVAL] Loaded LoRA adapter: {lora_path}")
    else:
        raise SystemExit(f"LoRA adapter not found: {lora_path}")

    FastVisionModel.for_inference(model)

    samples = build_samples(data_root, max_samples)
    if not samples:
        raise SystemExit("No samples found. Check data paths.")

    agg = {
        "total_samples": 0,
        "input_samples": len(samples),
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
        "skipped_bad_images": 0,
        "bad_image_rate": 0.0,
    }
    json_ok = 0
    empty_pred = 0
    empty_gt = 0
    bad_image = 0
    pred_chars_sum = 0
    pred_tokens_sum = 0
    diag_samples: List[Dict[str, Any]] = []

    with log_path.open("w", encoding="utf-8") as log_f:
        for idx, sample in enumerate(samples, start=1):
            prompt_text = sample["messages"][0]["content"][0]["text"]
            image = _coerce_image(sample["messages"][0]["content"][1]["image"])
            target_text = sample["messages"][1]["content"][0]["text"]
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
                f"[POST_EVAL {idx}/{len(samples)}] "
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
    if agg["input_samples"]:
        agg["skipped_bad_images"] = bad_image
        agg["bad_image_rate"] = bad_image / agg["input_samples"]

    with summary_path.open("w", encoding="utf-8") as f:
        payload = {"summary": agg}
        if DIAG_VERBOSE and diag_samples:
            payload["diagnostics"] = diag_samples
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Post-eval summary:")
    print(json.dumps(agg, ensure_ascii=False, indent=2))
    if DIAG_VERBOSE and diag_samples:
        print("Post-eval diagnostics (samples):")
        print(json.dumps(diag_samples, ensure_ascii=False, indent=2))


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


def find_repo_dir() -> Path:
    cwd = Path.cwd()
    if (cwd / DATA_ROOT).exists():
        return cwd
    for parent in cwd.parents:
        if (parent / DATA_ROOT).exists():
            return parent
    raise SystemExit("Repo directory not found. Run from the repo root.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a Qwen3-VL LoRA adapter.")
    parser.add_argument("--data-root", default=DATA_ROOT)
    parser.add_argument("--lora-path", default=DEFAULT_LORA_DIR)
    parser.add_argument("--max-samples", type=int, default=50)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--page-level", action="store_true", default=USE_PAGE_LEVEL)
    parser.add_argument("--crop-level", action="store_true", default=False)
    return parser.parse_args()


def main() -> None:
    set_seed(SEED)
    args = parse_args()
    global USE_PAGE_LEVEL
    if args.crop_level:
        USE_PAGE_LEVEL = False
    elif args.page_level:
        USE_PAGE_LEVEL = True

    repo_dir = find_repo_dir()
    data_root = repo_dir / args.data_root
    lora_path = repo_dir / args.lora_path
    run_eval(
        repo_dir=repo_dir,
        data_root=data_root,
        lora_path=lora_path,
        max_samples=args.max_samples,
        max_new_tokens=args.max_new_tokens,
    )


if __name__ == "__main__":
    main()
