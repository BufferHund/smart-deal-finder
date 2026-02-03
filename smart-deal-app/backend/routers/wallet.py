"""
Wallet API - Loyalty cards and receipts with unified AI client.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body
from services import storage
from services.ai_client import get_ai_client
import shutil
import os
import uuid
import json
import re
from datetime import datetime

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.post("/scan")
async def scan_card(file: UploadFile = File(...)):
    """Scan loyalty card using AI vision with retry and caching."""
    # 1. Save temp file
    temp_filename = f"scan_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Read image bytes
        with open(temp_path, "rb") as f:
            image_bytes = f.read()
        
        prompt = """Extract the 'store_name', 'card_number', and 'card_format' from this loyalty card image. 
'card_format' should be either 'QR' (if it looks like a QR code) or 'BARCODE' (if vertical bars). 
Return ONLY JSON format: {"store_name": "...", "card_number": "...", "card_format": "QR" | "BARCODE"}."""
        
        client = get_ai_client()
        data = await client.generate_json(
            prompt=prompt,
            image=image_bytes,
            model="gemini-2.5-flash",
            feature="wallet_card_scan"
        )
        return data
        
    except Exception as e:
        print(f"Card Scan Error: {e}")
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
    """Scan receipt using AI vision with retry logic."""
    # 1. Save temp file
    temp_filename = f"receipt_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Read image bytes
        with open(temp_path, "rb") as f:
            image_bytes = f.read()
        
        prompt = """Analyze this receipt image and extract the following details in JSON format:
- "store_name": The name of the store (string).
- "total_amount": The total amount paid (float, numeric only).
- "total_savings": Any discounts or savings mentioned (float, positive number). If none, 0.
- "purchase_date": The date of purchase in YYYY-MM-DD format (string). Use today's date if not visible.
- "items": A list of strings, where each string is an item name.

Return ONLY valid JSON."""
        
        client = get_ai_client()
        data = await client.generate_json(
            prompt=prompt,
            image=image_bytes,
            model="gemini-2.5-flash",
            feature="wallet_receipt_scan"
        )
        
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
        
    except Exception as e:
        print(f"Receipt Scan Error: {e}")
        return {"error": str(e)}
    # Note: Keep receipt image for history
