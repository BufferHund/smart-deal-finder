"""
Model Router - Multi-method extraction with usage tracking.
Supports: Gemini API / Local VLM (Ollama) / OCR Pipeline
"""
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
import os
import asyncio

class ExtractionMethod(Enum):
    GEMINI = "gemini"
    LOCAL_VLM = "local_vlm"
    OCR_PIPELINE = "ocr_pipeline"

# In-memory usage tracking (will persist to file)
USAGE_LOG_FILE = "dataset/usage_logs.json"
usage_logs: List[Dict] = []

def load_usage_logs():
    global usage_logs
    try:
        if os.path.exists(USAGE_LOG_FILE):
            with open(USAGE_LOG_FILE, 'r') as f:
                usage_logs = json.load(f)
    except:
        usage_logs = []

def save_usage_logs():
    os.makedirs(os.path.dirname(USAGE_LOG_FILE), exist_ok=True)
    with open(USAGE_LOG_FILE, 'w') as f:
        json.dump(usage_logs[-1000:], f)  # Keep last 1000 entries

def log_usage(
    method: ExtractionMethod,
    file_name: str,
    deal_count: int,
    duration_ms: int,
    tokens_used: int = 0,
    success: bool = True,
    error: str = None
):
    """Log extraction usage for analytics"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "method": method.value,
        "file_name": file_name,
        "deal_count": deal_count,
        "duration_ms": duration_ms,
        "tokens_used": tokens_used,
        "success": success,
        "error": error
    }
    usage_logs.append(entry)
    save_usage_logs()
    return entry

def get_usage_stats(days: int = 7) -> Dict:
    """Get usage statistics for the last N days"""
    load_usage_logs()
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    
    recent = [log for log in usage_logs 
              if datetime.fromisoformat(log["timestamp"]) > cutoff]
    
    stats = {
        "total_extractions": len(recent),
        "total_deals": sum(log.get("deal_count", 0) for log in recent),
        "total_tokens": sum(log.get("tokens_used", 0) for log in recent),
        "by_method": {},
        "success_rate": 0,
        "avg_duration_ms": 0
    }
    
    # Group by method
    for method in ExtractionMethod:
        method_logs = [l for l in recent if l["method"] == method.value]
        if method_logs:
            stats["by_method"][method.value] = {
                "count": len(method_logs),
                "deals": sum(l.get("deal_count", 0) for l in method_logs),
                "tokens": sum(l.get("tokens_used", 0) for l in method_logs),
                "avg_duration_ms": sum(l.get("duration_ms", 0) for l in method_logs) // len(method_logs),
                "success_rate": sum(1 for l in method_logs if l.get("success")) / len(method_logs) * 100
            }
    
    if recent:
        stats["success_rate"] = sum(1 for l in recent if l.get("success")) / len(recent) * 100
        stats["avg_duration_ms"] = sum(l.get("duration_ms", 0) for l in recent) // len(recent)
    
    return stats

async def extract_with_gemini(file_path: str, store_name: str, model_id: str = "gemini-2.5-flash-lite", region: Optional[List[float]] = None) -> Dict:
    """Extract using Gemini API via unified AI client."""
    from services.ai_client import get_ai_client
    import re
    from PIL import Image
    import io
    
    start_time = time.time()
    client = get_ai_client()
    
    # Handle Image Loading (PDF or Image)
    if file_path.lower().endswith('.pdf'):
        try:
            from pdf2image import convert_from_path
            # Convert first page only
            images = await asyncio.to_thread(convert_from_path, file_path, first_page=1, last_page=1)
            if images:
                image_obj = images[0]
            else:
                 raise ValueError("Could not convert PDF to image")
        except ImportError:
             raise ImportError("pdf2image not installed. Please install poppler-utils and pdf2image.")
    else:
        # Read image file directly
        image_obj = Image.open(file_path)
    
    # Apply Cropping if region provided [x_min, y_min, x_max, y_max]
    if region and len(region) == 4:
        width, height = image_obj.size
        x_min = int(region[0] * width)
        y_min = int(region[1] * height)
        x_max = int(region[2] * width)
        y_max = int(region[3] * height)
        
        # Validate coordinates
        if x_min < x_max and y_min < y_max:
             image_obj = image_obj.crop((x_min, y_min, x_max, y_max))
    
    # Convert to bytes for API
    img_byte_arr = io.BytesIO()
    image_obj.save(img_byte_arr, format='JPEG')
    file_data = img_byte_arr.getvalue()
    
    prompt = """You are an expert data extractor for German supermarket flyers.
Analyze the provided image and extract ALL product deals.

For EACH product, extract:
- product_name: Full name including brand (e.g., "Barilla Pasta")
- price: Numeric price (e.g., 1.99)
- original_price: numeric (original price if discounted)
- discount: text (e.g., "-30%", "20%")
- unit: text (e.g., "500 g", "1 L")
- brand: text 
- category: One of [Groceries, Drinks, Household, Personal Care, Other]
- bbox: [ymin, xmin, ymax, xmax] - Normalized bounding box coordinates (0-1) for the product area.

Return ONLY a valid JSON array with all products. Example format:
[
  {
    "product_name": "Coca-Cola",
    "price": 1.99,
    "unit": "1.5 L",
    "brand": "Coca-Cola",
    "category": "Drinks",
    "bbox": [0.1, 0.1, 0.2, 0.2]
  }
]

Extract ALL products visible on the page. Return ONLY the JSON array, no other text."""
    
    try:
        # Use unified client with retry and caching
        response = await client.generate(
            prompt=prompt,
            image=file_data,
            model=model_id,
            feature="brochure_extraction"
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        text = response.content
        
        # Parse JSON from response
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        
        deals = []
        if json_match:
            try:
                deals = json.loads(json_match.group())
            except:
                clean_text = text.replace("```json", "").replace("```", "").strip()
                try:
                    deals = json.loads(clean_text)
                except:
                    pass
        
        # Add store info and missing fields
        date_iso = datetime.now().isoformat()
        
        # Process deals: Add metadata and CROP IMAGES
        for deal in deals:
            deal["store"] = store_name
            deal["extraction_method"] = "gemini"
            deal["currency"] = "EUR"
            deal["extraction_date"] = date_iso
            # Ensure price is present (even if 0) failure safety
            if "price" not in deal: deal["price"] = 0
            
            # --- Image Cropping Logic ---
            if "bbox" in deal:
                # Gemini returns [ymin, xmin, ymax, xmax] usually, but let's check format
                # Our cropper expects [xmin, ymin, xmax, ymax]
                # Let's normalize assuming Gemini follows standard PDF/Vision bbox [ymin, xmin, ymax, xmax] 
                # Wait, Gemini 1.5 usually uses [ymin, xmin, ymax, xmax]. 
                # But let's verify visual alignment.
                # Standard convention for our system: [xmin, ymin, xmax, ymax]
                
                # If the prompting was ambiguous, let's assume [ymin, xmin, ymax, xmax] as per Gemini defaults
                # But we asked for it in the prompt without specifying order explicitly aside from example.
                # Actually, in the prompt above I wrote: "bbox: [ymin, xmin, ymax, xmax]"
                
                bbox = deal.get("bbox")
                if bbox and len(bbox) == 4:
                    # Convert [ymin, xmin, ymax, xmax] -> [xmin, ymin, xmax, ymax] for our cropper
                    # ymin, xmin, ymax, xmax = bbox
                    # cropper needs: x_min, y_min, x_max, y_max
                    
                    # Gemini default is [y1, x1, y2, x2] (normalized 0-1000 usually, but here 0-1 requested)
                    # Let's map it:
                    # x_min = bbox[1]
                    # y_min = bbox[0]
                    # x_max = bbox[3]
                    # y_max = bbox[2]
                    
                    # BUT: To be safe and avoid confusion, the prompt example was: [0.1, 0.1, 0.2, 0.2]
                    # Let's just swap appropriately.
                    
                    # Re-mapping to [xmin, ymin, xmax, ymax]
                    # Input (Gemini): [ymin, xmin, ymax, xmax]
                    reordered_bbox = [bbox[1], bbox[0], bbox[3], bbox[2]]
                    
                    image_url = crop_product_image(
                        source_image_path=file_path,
                        bbox=reordered_bbox,
                        store=store_name,
                        product_name=deal.get("product_name", "unknown")
                    )
                    
                    if image_url:
                        deal["image_url"] = image_url
                        
            # -----------------------------

        log_usage(
            method=ExtractionMethod.GEMINI,
            file_name=os.path.basename(file_path),
            deal_count=len(deals),
            duration_ms=duration_ms,
            tokens_used=response.tokens_used
        )
        
        return {
            "deals": deals, 
            "method": "gemini", 
            "model": model_id,
            "duration_ms": duration_ms,
            "cached": response.cached,
            "raw_input": prompt,
            "raw_response": text
        }
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_usage(
            method=ExtractionMethod.GEMINI,
            file_name=os.path.basename(file_path),
            deal_count=0,
            duration_ms=duration_ms,
            success=False,
            error=str(e)
        )
        raise

async def extract_with_local_vlm(file_path: str, store_name: str, model_id: str = "llava:7b", endpoint: str = "http://localhost:11434", region: Optional[List[float]] = None) -> Dict:
    """Extract using local VLM (Ollama with LLaVA)"""
    from extractors.ollama_extractor import extract_with_ollama
    from PIL import Image
    import numpy as np
    
    start_time = time.time()
    
    try:
        # Load image
        if file_path.lower().endswith('.pdf'):
            from pdf2image import convert_from_path
            # Convert first page only for now
            images = await asyncio.to_thread(convert_from_path, file_path, first_page=1, last_page=1)
            if not images:
                raise ValueError("Empty PDF")
            img = images[0]
        else:
            img = Image.open(file_path)
        
        # Apply Cropping if region provided
        if region and len(region) == 4:
            width, height = img.size
            x_min = int(region[0] * width)
            y_min = int(region[1] * height)
            x_max = int(region[2] * width)
            y_max = int(region[3] * height)
            if x_min < x_max and y_min < y_max:
                img = img.crop((x_min, y_min, x_max, y_max))

        # Convert to numpy array for extractor
        img_array = np.array(img)
        
        # Run in thread since it might be blocking
        result = await asyncio.to_thread(
            extract_with_ollama,
            image_array=img_array,
            model_id=model_id, 
            language="German"
        )
        
        deals = result.get("deals", [])
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_usage(
            method=ExtractionMethod.LOCAL_VLM,
            file_name=os.path.basename(file_path),
            deal_count=0,
            duration_ms=duration_ms,
            success=False,
            error=str(e)
        )
        raise ValueError(f"Local VLM failed: {e}")
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    date_iso = datetime.now().isoformat()
    for deal in deals:
        deal["store"] = store_name
        deal["extraction_method"] = "local_vlm"
        deal["currency"] = "EUR"
        deal["extraction_date"] = date_iso
    
    log_usage(
        method=ExtractionMethod.LOCAL_VLM,
        file_name=os.path.basename(file_path),
        deal_count=len(deals),
        duration_ms=duration_ms
    )
    
    return {
        "deals": deals, 
        "method": "local_vlm", 
        "duration_ms": duration_ms,
        "raw_input": result.get("raw_input", "Ollama prompt"),
        "raw_response": result.get("raw_response", "")
    }

async def extract_with_ocr(file_path: str, store_name: str) -> Dict:
    """Extract using OCR pipeline (Tesseract + regex parsing)"""
    import subprocess
    import re
    
    start_time = time.time()
    deals = []
    
    try:
        # Convert PDF to image if needed
        if file_path.endswith('.pdf'):
            from pdf2image import convert_from_path
            # Use to_thread for blocking conversion
            images = await asyncio.to_thread(convert_from_path, file_path, first_page=1, last_page=3)
            temp_img = "/tmp/ocr_temp.png"
            images[0].save(temp_img, 'PNG')
            img_path = temp_img
        else:
            img_path = file_path
        
        # Run Tesseract OCR in a thread
        def _run_tesseract():
            return subprocess.run(
                ['tesseract', img_path, 'stdout', '-l', 'deu+eng'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
        result = await asyncio.to_thread(_run_tesseract)
        text = result.stdout
        
        # Parse prices with regex
        # Pattern: product name followed by price
        price_pattern = r'([A-Za-zäöüÄÖÜß\s]+)\s*(\d+[,\.]\d{2})\s*€?'
        matches = re.findall(price_pattern, text)
        
        date_iso = datetime.now().isoformat()
        for match in matches:
            product = match[0].strip()
            price = match[1].replace(',', '.')
            
            if len(product) > 3 and float(price) < 100:  # Basic validation
                deals.append({
                    "product_name": product,
                    "price": float(price),
                    "store": store_name,
                    "category": "Other",
                    "extraction_method": "ocr_pipeline",
                    "currency": "EUR",
                    "extraction_date": date_iso
                })
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log_usage(
            method=ExtractionMethod.OCR_PIPELINE,
            file_name=os.path.basename(file_path),
            deal_count=0,
            duration_ms=duration_ms,
            success=False,
            error=str(e)
        )
        raise ValueError(f"OCR pipeline failed: {e}")
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    log_usage(
        method=ExtractionMethod.OCR_PIPELINE,
        file_name=os.path.basename(file_path),
        deal_count=len(deals),
        duration_ms=duration_ms
    )
    
    return {
        "deals": deals, 
        "method": "ocr_pipeline", 
        "duration_ms": duration_ms,
        "raw_input": "Tesseract OCR Command",
        "raw_response": text
    }

async def extract_deals(file_path: str, store_name: str, method: ExtractionMethod, model_id: str = None, region: Optional[List[float]] = None) -> Dict:
    """Main extraction router"""
    if method == ExtractionMethod.GEMINI:
        return await extract_with_gemini(file_path, store_name, model_id=model_id or "gemini-2.5-flash-lite", region=region)
    elif method == ExtractionMethod.LOCAL_VLM:
        return await extract_with_local_vlm(file_path, store_name, model_id=model_id or "llava:7b", region=region)
    else:
        return await extract_with_ocr(file_path, store_name)

# Load usage logs on import
load_usage_logs()
