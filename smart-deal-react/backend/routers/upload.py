from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from pydantic import BaseModel
import shutil
import os
import hashlib
import numpy as np
from PIL import Image
from typing import List, Optional, Any
from extractors.gemini_extractor import extract_with_gemini
from preprocessing.pdf_processor import convert_pdf_to_images
from services import storage
from db import db

router = APIRouter()

class Deal(BaseModel):
    product_name: Optional[str] = "Unknown"
    price: Optional[str] = "0.00"
    discount: Optional[str] = None
    unit: Optional[str] = None
    original_price: Optional[str] = None
    confidence: Optional[float] = 0.95
    source: Optional[str] = "gemini"
    model: Optional[str] = None
    store: Optional[str] = None 

class ExtractionResponse(BaseModel):
    deals: List[Deal]
    num_deals: int
    cached: bool = False

def calculate_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@router.post("/upload", response_model=ExtractionResponse)
async def upload_file(
    file: UploadFile = File(...),
    store_name: str = Form("Unknown Store"),
    visibility: str = Form("public"),
    force_refresh: str = Form("false")
):
    # Manual conversion because FormData sends booleans as strings "true"/"false"
    is_force_refresh = force_refresh.lower() == "true"
    print(f"DEBUG: Upload request received. File: {file.filename}, Raw Refresh Param: '{force_refresh}', Parsed: {is_force_refresh}")

    # 1. Save upload temporarily to calculate hash
    UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Calculate Hash & Check Cache
        file_hash = calculate_file_hash(file_path)
        
        # Check if hash exists in DB
        existing_upload = db.execute_query("SELECT id, deal_count FROM uploads WHERE file_hash = %s", (file_hash,))
        
        if existing_upload and not is_force_refresh:
            print(f"DEBUG: Cache Hit! File hash {file_hash} exists. Returning DB data.")
            # Hash found! Return cached deals
            upload_id = existing_upload[0]['id']
            cached_deals = db.execute_query("SELECT * FROM deals WHERE upload_id = %s", (upload_id,))
            
            # Format deals
            formatted_deals = []
            for d in cached_deals:
                formatted_deals.append({
                    "product_name": d['product_name'],
                    "price": str(d['price']),
                    "discount": None, # We didn't save discount column in v1 schema, could add later
                    "unit": d['unit'],
                    "original_price": d['original_price'],
                    "store": d['store'],
                    "source": "cache"
                })
                
            return {
                "deals": formatted_deals,
                "num_deals": len(formatted_deals),
                "cached": True
            }
        
        if existing_upload and is_force_refresh:
             print(f"DEBUG: File exists but Force Refresh requested. Re-processing hash {file_hash}...")
             upload_id = existing_upload[0]['id']
             # Clear old deals for this upload
             db.execute_query("DELETE FROM deals WHERE upload_id = %s", (upload_id,))
             # We will re-use the upload_id to insert new deals later
        else:
             upload_id = None

        # 3. Not in Cache -> Process File
        image_array = None
        if file.filename.lower().endswith(".pdf"):
            images = convert_pdf_to_images(file_path)
            if images:
                image_array = images[0] 
        else:
            pil_image = Image.open(file_path).convert('RGB')
            image_array = np.array(pil_image)
                
        if image_array is None:
            raise HTTPException(400, "Could not process file as image or PDF")

        # 4. Get API Key
        api_key = storage.get_api_key()
        if not api_key:
             api_key = os.getenv("GOOGLE_API_KEY")
             if not api_key:
                 raise HTTPException(400, "Gemini API Key not set.")

        print(f"DEBUG: Starting extraction for file: {file.filename}")

        # 5. Extract
        result = extract_with_gemini(image_array, api_key=api_key)
        deals = result.get('deals', [])
        
        print(f"DEBUG: Extraction complete. Found {len(deals)} deals.")
        
        # 6. Log Upload (Get ID)
        if not upload_id:
            upload_id = storage.log_upload(file.filename, len(deals), file_path, file_hash, visibility=visibility)
        else:
            # Update existing upload record timestamp/count if needed
             db.execute_query("UPDATE uploads SET timestamp = CURRENT_TIMESTAMP, deal_count = %s WHERE id = %s", (len(deals), upload_id))
        
        # 7. Save Deals with Upload ID
        storage.save_active_deals(deals, store_name=store_name, upload_id=upload_id, visibility=visibility)
        
        return {
            "deals": deals,
            "num_deals": len(deals),
            "cached": False
        }
        
    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")
