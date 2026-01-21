"""
Simple local storage service for SmartDeal Consumer data.
Refactored to use TinyDB.
"""
from typing import Dict, List, Any
from db import db

# Initialize default user document if not exists
DEFAULT_USER_ID = "default_user"
User = db.query
users_table = db.users
session_table = db.session

def _get_user_doc():
    """Get the default user document, create if not missing."""
    res = users_table.search(User.user_id == DEFAULT_USER_ID)
    if not res:
        doc = {
            "user_id": DEFAULT_USER_ID,
            "shopping_list": [],
            "favorites": [],
            "settings": {"notification_threshold": 0.2, "gemini_api_key": ""}
        }
        users_table.insert(doc)
        return doc
    return res[0]

def _update_user_doc(updates: Dict):
    """Update the user document."""
    users_table.update(updates, User.user_id == DEFAULT_USER_ID)

def add_to_list(item: str):
    """Add an item to the shopping list."""
    doc = _get_user_doc()
    current_list = doc.get("shopping_list", [])
    if item not in current_list:
        current_list.append(item)
        _update_user_doc({"shopping_list": current_list})

def remove_from_list(item: str):
    """Remove an item from the shopping list."""
    doc = _get_user_doc()
    current_list = doc.get("shopping_list", [])
    if item in current_list:
        current_list.remove(item)
        _update_user_doc({"shopping_list": current_list})

def get_shopping_list() -> List[str]:
    """Get the current shopping list."""
    return _get_user_doc().get("shopping_list", [])

def toggle_favorite(deal_id: str):
    """Toggle a deal as favorite."""
    doc = _get_user_doc()
    favorites = doc.get("favorites", [])
    
    if deal_id in favorites:
        favorites.remove(deal_id)
    else:
        favorites.append(deal_id)
        
    _update_user_doc({"favorites": favorites})

def get_favorites() -> List[str]:
    """Get list of favorite deal IDs."""
    return _get_user_doc().get("favorites", [])

def get_api_key() -> str:
    """Get the saved Gemini API key."""
    return _get_user_doc().get("settings", {}).get("gemini_api_key", "")

def save_api_key(api_key: str):
    """Save the Gemini API key."""
    doc = _get_user_doc()
    settings = doc.get("settings", {})
    settings["gemini_api_key"] = api_key
    _update_user_doc({"settings": settings})

# --- Active Scan Session Storage ---
# We store active deals in a single document in 'session' table with id='active_session'

def save_active_deals(deals: List[Dict]):
    """Save the current active extracted deals."""
    session_table.upsert(
        {'id': 'active_session', 'deals': deals}, 
        User.id == 'active_session'
    )

def get_active_deals() -> List[Dict]:
    """Load the last active extracted deals."""
    res = session_table.search(User.id == 'active_session')
    if res:
        return res[0].get('deals', [])
    return []
