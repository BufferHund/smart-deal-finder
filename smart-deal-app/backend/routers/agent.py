"""
Agent API - AI-powered shopping agent with unified AI client.
Includes: daily briefing, fridge scan, and agentic recommendations.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from typing import List
from services import storage, mock_generator
from services.ai_client import get_ai_client
import os
import random
import shutil
import uuid
import re
import json

router = APIRouter(prefix="/api/agent", tags=["agent"])


class Preferences(BaseModel):
    disliked_items: List[str] = []


@router.get("/preferences")
def get_preferences():
    return storage.get_user_settings()


@router.post("/preferences")
def update_preferences(prefs: Preferences):
    storage.update_user_settings({"disliked_items": prefs.disliked_items})
    return {"status": "ok"}


@router.post("/generate-mock")
def generate_mock_data():
    """Generates 2000 mock deals"""
    result = mock_generator.generate_mock_deals(2000)
    return {"status": "ok", "generated": len(result)}


@router.get("/briefing")
async def get_daily_briefing():
    """Generates personalized daily briefing using unified AI client."""
    client = get_ai_client()
    
    # 1. Gather Context
    watchlist = storage.get_watchlist()
    deals_data = storage.get_active_deals()
    deals = deals_data.get("deals", [])
    
    # 2. Find relevant deals
    relevant_deals = []
    for item in watchlist:
        for deal in deals:
            if item.lower() in deal['product_name'].lower():
                relevant_deals.append(f"{deal['product_name']} at {deal['store']} ({deal['price']}€)")
    
    relevant_deals = relevant_deals[:5]
    top_deals = [f"{d['product_name']} ({d['price']}€)" for d in deals[:5]]
    
    # 3. Prompt AI
    try:
        prompt = f"""You are a proactive Shopping Agent.
User's Watchlist matches: {', '.join(relevant_deals) if relevant_deals else 'None'}
Top Market Deals: {', '.join(top_deals)}

Task: Write a ONE-SENTENCE, exciting "Good Morning" message to the user.
If there are watchlist matches, highlight the best one.
If not, highlight a great market deal.
Use emojis. Keep it under 20 words."""
        
        response = await client.generate(
            prompt=prompt,
            model="gemini-2.5-flash",
            feature="agent_briefing"
        )
        return {"briefing": response.content.strip()}
        
    except Exception as e:
        print(f"Agent Error: {e}")
        if relevant_deals:
            return {"briefing": f"Good news! 🔔 Found deals for: {relevant_deals[0]}!"}
        return {"briefing": "Happy shopping! 🛍️ Check out the fresh offers below."}


@router.post("/scan-fridge")
async def scan_fridge(file: UploadFile = File(...)):
    """Scan fridge/food photo using AI vision with retry."""
    temp_filename = f"fridge_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    os.makedirs("uploads", exist_ok=True)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        with open(temp_path, "rb") as f:
            image_bytes = f.read()
        
        prompt = """Analyze this fridge/food photo. 
1. List the visible ingredients.
2. Suggest ONE delicious recipe I can make with these (and maybe a few common extras).
3. Tell me what ONE KEY ingredient I am missing for that recipe.

Return JSON: {"ingredients": ["..."], "recipe_name": "...", "missing_ingredient": "...", "message": "Short friendly text explaining the idea."}"""
        
        client = get_ai_client()
        data = await client.generate_json(
            prompt=prompt,
            image=image_bytes,
            model="gemini-2.5-flash",
            feature="agent_fridge_scan"
        )
        return data
            
    except Exception as e:
        print(f"Fridge Scan Error: {e}")
        return {"message": f"I couldn't quite see what's in there. Error: {str(e)}", "ingredients": [], "recipe_name": "", "missing_ingredient": ""}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


class RecommendRequest(BaseModel):
    shopping_list: List[str] = []
    limit: int = 10


@router.post("/recommend")
async def get_agentic_recommendations(req: RecommendRequest):
    """Agentic Recommendation Engine with unified AI client."""
    client = get_ai_client()
    
    try:
        # 1. Gather ALL context
        shopping_list = req.shopping_list or storage.get_shopping_list()
        settings = storage.get_user_settings()
        disliked = settings.get("disliked_items", [])
        watchlist = storage.get_watchlist()
        deals_data = storage.get_active_deals()
        all_deals = deals_data.get("deals", [])[:100]
        
        if not all_deals:
            return {"recommendations": [], "reasoning": "No deals available.", "agent_mode": True}
        
        # 2. Build Agent Prompt
        deals_summary = "\n".join([
            f"- ID:{i} | {d['product_name']} | €{d['price']} | {d['store']} | {d.get('category', 'Other')}"
            for i, d in enumerate(all_deals)
        ])
        
        prompt = f"""You are a smart Shopping Agent. Recommend the BEST deals for this user.

## User Context
- Shopping List: {', '.join(shopping_list) if shopping_list else 'Empty'}
- Watchlist: {', '.join(watchlist) if watchlist else 'None'}
- Dislikes (NEVER recommend): {', '.join(disliked) if disliked else 'None'}

## Available Deals
{deals_summary}

## Rules
1. Pick TOP {req.limit} most relevant deals.
2. Priority: Watchlist > Shopping list > Good value.
3. Never recommend disliked items.

## Output (JSON only)
IMPORTANT: Keep ALL text VERY SHORT. Reasons max 5 words. Reasoning max 10 words.
Use tags: [List], [Watch], [Deal], [Fresh], [Popular]

{{
    "reasoning": "Found 3 list matches, 2 great deals.",
    "recommendations": [
        {{"deal_id": 0, "score": 95, "reason": "[List] On your list"}},
        {{"deal_id": 5, "score": 88, "reason": "[Deal] 40% off today"}}
    ]
}}"""
        
        result = await client.generate_json(
            prompt=prompt,
            model="gemini-2.5-flash",
            feature="agent_recommend"
        )
        
        # Enrich recommendations with full deal data
        enriched_recs = []
        for rec in result.get("recommendations", []):
            deal_id = rec.get("deal_id", 0)
            if 0 <= deal_id < len(all_deals):
                deal = all_deals[deal_id].copy()
                deal["ai_score"] = rec.get("score", 50)
                deal["ai_reason"] = rec.get("reason", "")
                enriched_recs.append(deal)
        
        return {
            "recommendations": enriched_recs,
            "reasoning": result.get("reasoning", ""),
            "agent_mode": True
        }
            
    except Exception as e:
        print(f"Agent Recommend Error: {e}")
        deals_data = storage.get_active_deals()
        all_deals = deals_data.get("deals", [])
        return {
            "recommendations": random.sample(all_deals, min(req.limit, len(all_deals))) if all_deals else [],
            "reasoning": f"Error: {str(e)}",
            "agent_mode": False
        }
