"""
Gemini Multi-Model Comparison Service.
Supports comparing extraction results across different Gemini model variants.
"""
import google.generativeai as genai
from typing import List, Dict, Any
from dataclasses import dataclass
import time
import json
import re
import base64
import os

@dataclass
class GeminiModelSpec:
    model_id: str
    display_name: str
    cost_per_1k_tokens: float  # Input cost in USD
    description: str

# Available Gemini models for comparison (Restricted to 2.5+)
GEMINI_MODELS = [
    GeminiModelSpec(
        "gemini-2.5-flash",
        "Gemini 2.5 Flash",
        0.00001,
        "Latest 2.5 flash, fast & smart"
    ),
    GeminiModelSpec(
        "gemini-2.5-pro",
        "Gemini 2.5 Pro", 
        0.00125,
        "Most capable 2.5, highest accuracy"
    ),
    GeminiModelSpec(
        "gemini-3-flash-preview",
        "Gemini 3 Flash",
        0.00002,
        "Next-gen speed (Preview)"
    ),
    GeminiModelSpec(
        "gemini-3-pro-preview",
        "Gemini 3 Pro",
        0.00200,
        "Next-gen reasoning (Preview)"
    ),
]

def get_available_models() -> List[Dict]:
    """Return list of available models for frontend selection"""
    return [
        {
            "model_id": m.model_id,
            "display_name": m.display_name,
            "cost_per_1k_tokens": m.cost_per_1k_tokens,
            "description": m.description
        }
        for m in GEMINI_MODELS
    ]

EXTRACTION_PROMPT = """Extract all supermarket deals from this flyer page.
Return ONLY valid JSON (no extra text).
Schema (JSON array of objects):
[
  {
    "product_name": string | null,
    "price": string | number | null,
    "discount": string | null,
    "unit": string | null,
    "category": string | null
  }
]
Rules:
- Use null if a field is missing.
- Keep prices as numbers or numeric strings (e.g., "1.99").
- Product name should focus on the item, not marketing text.
- Category should be one of: Fruit & Veg, Meat & Fish, Dairy, Bakery, Drinks, Snacks, Household, Other
"""

async def extract_with_model(
    file_path: str,
    store_name: str,
    model_id: str,
    api_key: str
) -> Dict[str, Any]:
    """Extract deals using a specific Gemini model"""
    start_time = time.time()
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_id)
    
    # Read file
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    file_b64 = base64.b64encode(file_data).decode('utf-8')
    
    # Determine mime type
    mime = "application/pdf" if file_path.endswith('.pdf') else "image/jpeg"
    if file_path.endswith('.png'):
        mime = "image/png"
    
    import asyncio
    try:
        print(f"DEBUG: Starting extraction for {model_id}...")
        loop = asyncio.get_running_loop()
        
        def _call_gemini():
            return model.generate_content([
                {"mime_type": mime, "data": file_b64},
                EXTRACTION_PROMPT
            ])

        # Run synchronous API call in a thread to avoid blocking
        response = await loop.run_in_executor(None, _call_gemini)
        
        print(f"DEBUG: Finished extraction for {model_id}")
        
        duration_ms = int((time.time() - start_time) * 1000)
        text = response.text
        
        # Clean markdown code blocks
        clean_text = text.replace('```json', '').replace('```', '').strip()
        
        # Try finding JSON array
        json_match = re.search(r'\[.*\]', clean_text, re.DOTALL)
        deals = []
        if json_match:
            try:
                deals = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Fallback: try parsing the whole text if regex failed effectively
                try:
                    deals = json.loads(clean_text)
                except:
                    pass
        elif clean_text.startswith('[') and clean_text.endswith(']'):
             try:
                deals = json.loads(clean_text)
             except:
                pass
        
        # Add metadata
        for deal in deals:
            deal["store"] = store_name
            deal["extraction_model"] = model_id
        
        # Estimate tokens (rough approximation)
        input_tokens = len(file_data) // 4  # ~4 bytes per token for images
        output_tokens = len(text.split())
        
        # Get model cost
        model_spec = next((m for m in GEMINI_MODELS if m.model_id == model_id), None)
        cost = 0.0
        if model_spec:
            cost = (input_tokens / 1000) * model_spec.cost_per_1k_tokens
        
        # Save log for debugging
        log_dir = "/tmp/gemini_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{model_id}_{int(time.time())}.txt"
        with open(log_file, "w") as f:
            f.write(f"PROMPT:\n{EXTRACTION_PROMPT}\n\nRESPONSE:\n{text}")
            
        return {
            "success": True,
            "model_id": model_id,
            "deals": deals,
            "deal_count": len(deals),
            "duration_ms": duration_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": round(cost, 6),
            "raw_input": EXTRACTION_PROMPT,
            "raw_response": text,
            "log_file": log_file
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return {
            "success": False,
            "model_id": model_id,
            "deals": [],
            "deal_count": 0,
            "duration_ms": duration_ms,
            "error": str(e),
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0
        }

async def compare_gemini_models(
    file_path: str,
    store_name: str,
    model_ids: List[str],
    api_key: str
) -> Dict[str, Any]:
    """Run extraction with multiple Gemini models and compare results"""
    import asyncio
    
    tasks = [
        extract_with_model(file_path, store_name, model_id, api_key)
        for model_id in model_ids
    ]
    
    results_list = await asyncio.gather(*tasks)
    results = {res["model_id"]: res for res in results_list}
    
    # Determine winner by deal count
    valid_results = {k: v for k, v in results.items() if v["success"]}
    winner = None
    if valid_results:
        best = max(valid_results.items(), key=lambda x: (x[1]["deal_count"], -x[1]["duration_ms"]))
        winner = {
            "model_id": best[0],
            "deal_count": best[1]["deal_count"],
            "duration_ms": best[1]["duration_ms"]
        }
    
    # Calculate totals
    total_cost = sum(r.get("estimated_cost", 0) for r in results.values())
    total_duration = sum(r.get("duration_ms", 0) for r in results.values())
    
    return {
        "results": results,
        "winner": winner,
        "total_cost": round(total_cost, 6),
        "total_duration_ms": total_duration,
        "models_tested": len(model_ids)
    }

def calculate_metrics(gt_deals: List[Dict], pred_deals: List[Dict]) -> Dict[str, float]:
    """Calculate precision, recall, F1 for deal extraction (like benchmark)"""
    if not gt_deals:
        return {"precision": 0, "recall": 0, "f1": 0}
    
    # Simple name matching
    matched = 0
    for pred in pred_deals:
        pred_name = (pred.get("product_name") or "").lower()
        for gt in gt_deals:
            gt_name = (gt.get("product_name") or "").lower()
            # Fuzzy match: check if significant overlap
            if pred_name and gt_name:
                if pred_name in gt_name or gt_name in pred_name:
                    matched += 1
                    break
    
    precision = matched / len(pred_deals) if pred_deals else 0
    recall = matched / len(gt_deals) if gt_deals else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "matched_count": matched,
        "pred_count": len(pred_deals),
        "gt_count": len(gt_deals)
    }
