from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from services import storage
import shutil
import os
import uuid
import google.generativeai as genai

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

@router.post("/scan")
async def scan_card(file: UploadFile = File(...)):
    # 1. Save temp file
    temp_filename = f"scan_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Use Gemini Vision to extract details
    api_key = storage.get_api_key() or os.getenv("GEMINI_API_KEY")
    if not api_key:
         return {"error": "API Key missing"}
         
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Upload file to Gemini (or pass bytes if supported, but file API is safer for large images)
        # Note: genai.upload_file is the preferred way for multimodal
        # But for simplicity/speed let's try passing the image data directly if the library version supports it
        # The prompt:
        prompt = "Extract the 'store_name', 'card_number', and 'card_format' from this loyalty card image. 'card_format' should be either 'QR' (if it looks like a QR code) or 'BARCODE' (if vertical bars). Return ONLY JSON format: {\"store_name\": \"...\", \"card_number\": \"...\", \"card_format\": \"QR\" | \"BARCODE\"}."
        
        # For simplicity in this env, we load the image as PIL
        from PIL import Image
        img = Image.open(temp_path)
        
        response = model.generate_content([prompt, img])
        text = response.text
        
        # Clean up JSON
        import json
        import re
        
        # Find JSON in markdown code block if present
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data
        else:
            # Fallback
            return {"store_name": "Unknown", "card_number": text, "card_format": "BARCODE"}
            
    except Exception as e:
        print(f"OCR Error: {e}")
        return {"error": str(e)}
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/")
def get_cards():
    return {"cards": storage.get_cards()}

@router.post("/")
def add_card(
    store_name: str = Body(..., embed=True), 
    card_number: str = Body(..., embed=True),
    card_format: str = Body("BARCODE", embed=True)
):
    # JSON based add
    storage.add_card(store_name, card_number, card_format)
    return {"status": "ok", "cards": storage.get_cards()}

@router.delete("/{card_id}")
def delete_card(card_id: int):
    storage.delete_card(card_id)
    return {"status": "ok", "cards": storage.get_cards()}

@router.get("/receipts")
def get_receipts():
    return {"receipts": storage.get_receipts()}

@router.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int):
    storage.delete_receipt(receipt_id)
    return {"status": "ok", "receipts": storage.get_receipts()}

@router.post("/receipts/scan")
async def scan_receipt(file: UploadFile = File(...)):
    # 1. Save temp file
    temp_filename = f"receipt_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Use Gemini Vision to extract details
    api_key = storage.get_ai_token()
    if not api_key:
         return {"error": "API Key missing or rate limit exceeded"}
         
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = """
        Analyze this receipt image and extract the following details in JSON format:
        - "store_name": The name of the store (string).
        - "total_amount": The total amount paid (float, numeric only).
        - "total_savings": Any discounts or savings mentioned (float, positive number). If none, 0.
        - "purchase_date": The date of purchase in YYYY-MM-DD format (string). Use today's date if not visible.
        - "items": A list of strings, where each string is an item name.
        
        Return ONLY valid JSON.
        """
        
        from PIL import Image
        img = Image.open(temp_path)
        
        response = model.generate_content([prompt, img])
        text = response.text
        
        # Clean up JSON
        import json
        import re
        from datetime import datetime
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            
            # Validate/Fallback
            store = data.get("store_name", "Unknown Store")
            try:
                total = float(str(data.get("total_amount", 0)).replace(',', '.'))
            except:
                total = 0.0
            date = data.get("purchase_date") or datetime.now().strftime("%Y-%m-%d")
            items = data.get("items", [])
            
            # Save to DB
            storage.add_receipt(store, total, date, temp_filename, items)
            
            return {"status": "ok", "receipts": storage.get_receipts()}
        else:
            return {"error": "Failed to parse receipt data"}
            
    except Exception as e:
        print(f"Receipt OCR Error: {e}")
        return {"error": str(e)}
    # Note: We prefer to keep the receipt image for history, so no deletion here

