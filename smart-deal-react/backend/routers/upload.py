from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from pydantic import BaseModel
import shutil
import os
import tempfile
import numpy as np
import cv2
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

class ExtractionResponse(BaseModel):
    deals: List[Deal]
    num_deals: int

@router.post("/upload", response_model=ExtractionResponse)
async def upload_file(file: UploadFile = File(...)):
    # 1. Save upload to temp
    # Create temp dir if not exists
    os.makedirs("/tmp/smartdeal", exist_ok=True)
    tmp_path = f"/tmp/smartdeal/{file.filename}"
    
    try:
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
        # 2. Process File (Image/PDF)
        image_array = None
        if file.filename.lower().endswith(".pdf"):
            images = convert_pdf_to_images(tmp_path)
            if images:
                image_array = images[0] # First page only for demo
        else:
            # Assume image
            pil_image = Image.open(tmp_path).convert('RGB')
            image_array = np.array(pil_image)
                
        if image_array is None:
            raise HTTPException(400, "Could not process file as image or PDF")

        # 3. Get API Key from DB
        api_key = storage.get_api_key()
        if not api_key:
             # Fallback to env var if available 
             api_key = os.getenv("GOOGLE_API_KEY")
             if not api_key:
                 raise HTTPException(400, "Gemini API Key not set. Please configure it in settings.")

        # 4. Extract
        result = extract_with_gemini(image_array, api_key=api_key)
        
        # 5. Save to Session
        deals = result.get('deals', [])
        # Ensure deals match Pydantic model by filtering extra fields if necessary
        # Storage expects dicts, so we pass as is
        storage.save_active_deals(deals)
        
        return {
            "deals": deals,
            "num_deals": len(deals)
        }
        
    except Exception as e:
        print(f"Extraction error: {e}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
