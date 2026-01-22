from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from typing import List
from services import storage, mock_generator
import google.generativeai as genai
import os
import random
import shutil
import uuid
import re
import json
from PIL import Image

router = APIRouter(prefix="/api/agent", tags=["agent"])

class Preferences(BaseModel):
    disliked_items: List[str] = []

@router.get("/preferences")
def get_preferences():
    settings = storage.get_user_settings()
    return {"disliked_items": settings.get("disliked_items", [])}

@router.post("/preferences")
def update_preferences(prefs: Preferences):
    storage.update_user_settings({"disliked_items": prefs.disliked_items})
    return {"status": "ok", "disliked_items": prefs.disliked_items}

@router.post("/mock-data")
def generate_mock_data():
    """Generates 2000 mock deals"""
    try:
        count = mock_generator.generate_mock_data(2000)
        return {"status": "ok", "message": f"Generated {count} mock deals."}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/briefing")
def get_daily_briefing():
    """
    Generates a personalized daily briefing using Gemini.
    """
    api_key = storage.get_api_key() or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"briefing": "Good morning! Add your API Key in settings to get personalized AI tips."}

    # 1. Gather Context
    watchlist = storage.get_watchlist()
    deals_data = storage.get_active_deals() # {"deals": [...], "count": ...}
    deals = deals_data.get("deals", [])
    
    # 2. Find relevant deals
    relevant_deals = []
    for item in watchlist:
        for deal in deals:
            if item.lower() in deal['product_name'].lower():
                relevant_deals.append(f"{deal['product_name']} at {deal['store']} ({deal['price']}€)")
    
    # Limit context size
    relevant_deals = relevant_deals[:5]
    top_deals = [f"{d['product_name']} ({d['price']}€)" for d in deals[:5]]
    
    # 3. Prompt Gemini
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        You are a proactive Shopping Agent.
        User's Watchlist matches: {', '.join(relevant_deals) if relevant_deals else 'None'}
        Top Market Deals: {', '.join(top_deals)}
        
        Task: Write a ONE-SENTENCE, exciting "Good Morning" message to the user.
        If there are watchlist matches, highlight the best one.
        If not, highlight a great market deal.
        Use emojis. Keep it under 20 words.
        """
        
        response = model.generate_content(prompt)
        return {"briefing": response.text.strip()}
        
    except Exception as e:
        print(f"Agent Error: {e}")
        # Fallback if AI fails
        if relevant_deals:
            return {"briefing": f"Good news! 🔔 Found deals for: {relevant_deals[0]}!"}
        else:
            return {"briefing": "Happy shopping! 🛍️ Check out the fresh offers below."}

@router.post("/scan-fridge")
async def scan_fridge(file: UploadFile = File(...)):
    # 1. Save temp file
    temp_filename = f"fridge_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        api_key = storage.get_api_key() or os.getenv("GEMINI_API_KEY")
        if not api_key:
             return {"response": "API Key missing."}

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = """
        Analyze this fridge/food photo. 
        1. List the visible ingredients.
        2. Suggest ONE delicious recipe I can make with these (and maybe a few common extras).
        3. Tell me what ONE KEY ingredient I am missing for that recipe.
        
        Return JSON: {"ingredients": ["..."], "recipe_name": "...", "missing_ingredient": "...", "message": "Short friendly text explaining the idea."}
        """
        
        img = Image.open(temp_path)
        response = model.generate_content([prompt, img])
        text = response.text
        
        # Clean up JSON
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data
        else:
            return {"message": text, "ingredients": [], "recipe_name": "", "missing_ingredient": ""}
            
    except Exception as e:
        print(f"Fridge Scan Error: {e}")
        return {"response": f"I couldn't quite see what's in there. Error: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
