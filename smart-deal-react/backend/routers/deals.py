from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from services import storage
from services.history import PriceHistoryService
from services.chef import ChefService

router = APIRouter()
history_service = PriceHistoryService()
chef_service = ChefService()

# --- Models ---
class ShoppingItem(BaseModel):
    item: str

class WatchlistItem(BaseModel):
    item: str

class ApiKeyRequest(BaseModel):
    api_key: str

class ChatRequest(BaseModel):
    message: str

# --- Endpoints ---

@router.get("/deals/active")
def get_active_deals():
    return storage.get_active_deals()

@router.get("/deals/history")
def get_deal_history():
    # Return weekly best buys as summary
    return history_service.get_weekly_best_buys()

@router.get("/shopping-list", response_model=List[str])
def get_shopping_list():
    return storage.get_shopping_list()

@router.post("/shopping-list")
def add_shopping_item(item: ShoppingItem):
    storage.add_to_list(item.item)
    return {"status": "added", "list": storage.get_shopping_list()}

@router.delete("/shopping-list/{item}")
def remove_shopping_item(item: str):
    storage.remove_from_list(item)
    return {"status": "removed", "list": storage.get_shopping_list()}

@router.get("/watchlist", response_model=List[str])
def get_watchlist():
    return storage.get_watchlist()

@router.post("/watchlist")
def add_watchlist_item(item: WatchlistItem):
    storage.add_watchlist_item(item.item)
    return {"status": "added", "list": storage.get_watchlist()}

@router.delete("/watchlist/{item}")
def remove_watchlist_item(item: str):
    storage.remove_watchlist_item(item)
    return {"status": "removed", "list": storage.get_watchlist()}

@router.get("/settings/key")
def get_api_key_status():
    key = storage.get_api_key()
    return {"configured": bool(key), "masked": f"{key[:4]}...{key[-4:]}" if key else None}

@router.post("/settings/key")
def set_api_key(req: ApiKeyRequest):
    storage.save_api_key(req.api_key)
    storage.save_api_key(req.api_key)
    return {"status": "saved"}

@router.post("/settings/reset")
def reset_data():
    storage.reset_user_data()
    return {"status": "reset", "message": "All data cleared"}

@router.post("/settings/load-demo-data")
def load_demo_data():
    """Load 2000+ German demo deals into the database."""
    try:
        from services.mock_generator import generate_mock_data
        count = generate_mock_data(2000)
        return {"status": "ok", "message": f"Successfully loaded {count} demo deals"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/chat")
def chat_with_chef(req: ChatRequest):
    active_deals = storage.get_active_deals()
    
    # Simple intent recognition
    msg = req.message.lower()
    
    if "menu" in msg or "suggest" in msg or "dinner" in msg:
        result = chef_service.suggest_menu_from_deals(active_deals)
        return {"type": "menu", "data": result}
        
    elif "recipe" in msg:
        # Extract potential dish name (very naive)
        dish_name = msg.split("recipe")[-1].replace("for", "").strip()
        if not dish_name:
            dish_name = "something delicious"
        result = chef_service.generate_recipe_steps(dish_name)
        return {"type": "recipe", "data": result}

    elif "cook" in msg or "make" in msg or "plan" in msg:
        # "I want to cook Lasagna" -> Extract "Lasagna"
        # Naive extraction: take everything after the keyword
        keyword = "cook" if "cook" in msg else "make" if "make" in msg else "plan"
        dish_name = msg.split(keyword)[-1].strip()
        if not dish_name:
             dish_name = "dinner"
        
        result = chef_service.plan_meal(dish_name)
        return {"type": "meal_plan", "data": result}
        
    else:
        return {
            "type": "text", 
            "data": "I'm your AI Budget Chef! Ask me to 'suggest a menu' based on current deals, or ask for a 'recipe for [dish]'."
        }
