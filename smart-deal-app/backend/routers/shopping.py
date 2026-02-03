from fastapi import APIRouter, HTTPException, Body
from services import storage
from services.rag_service import find_product_matches, normalize_text, similarity_score
from typing import List, Dict
import re

router = APIRouter(prefix="/api/shopping-list", tags=["shopping"])

# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Fruit & Veg": ["apple", "banana", "orange", "tomato", "potato", "carrot", "onion", "lettuce", "cucumber", "pepper", "lemon", "avocado", "spinach", "broccoli", "fruit", "vegetable", "salad", "berry"],
    "Meat & Fish": ["chicken", "beef", "pork", "fish", "salmon", "tuna", "sausage", "bacon", "ham", "meat", "steak", "ground", "fillet", "shrimp"],
    "Dairy": ["milk", "cheese", "yogurt", "butter", "cream", "egg", "eggs", "dairy", "joghurt"],
    "Bakery": ["bread", "roll", "bun", "croissant", "cake", "pastry", "bagel", "toast"],
    "Drinks": ["water", "juice", "cola", "soda", "beer", "wine", "coffee", "tea", "drink", "beverage"],
    "Snacks": ["chips", "chocolate", "candy", "cookie", "biscuit", "nuts", "snack", "ice cream"],
    "Household": ["soap", "detergent", "paper", "tissue", "cleaner", "shampoo", "toothpaste"]
}

def guess_category(item: str) -> str:
    """Guess category based on item keywords"""
    item_lower = item.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in item_lower:
                return category
    return "Other"

def parse_unit_price(deal: Dict) -> float:
    """Calculate price per unit/kg if possible"""
    try:
        price = float(deal.get('price', 0))
        unit = deal.get('unit', '').lower()
        # Try to normalize to per-kg or per-piece
        if 'kg' in unit or '/kg' in unit:
            return price  # Already per kg
        elif 'g' in unit:
            # Extract grams
            match = re.search(r'(\d+)\s*g', unit)
            if match:
                grams = int(match.group(1))
                return (price / grams) * 1000  # Convert to per-kg
        return price  # Fallback to raw price
    except:
        return 999.0

@router.get("/")
def get_list():
    return storage.get_shopping_list()

@router.post("/")
def add_item(item: dict = Body(...)):
    storage.add_to_list(item.get("item"))
    return {"status": "ok", "list": storage.get_shopping_list()}

@router.delete("/{item_name}")
def delete_item(item_name: str):
    storage.remove_from_list(item_name)
    return {"status": "ok", "list": storage.get_shopping_list()}

@router.post("/optimize")
def optimize_list(items: List[str] = Body(..., embed=True)):
    """
    Smart optimization with category-based fallback:
    1. Try exact product match
    2. If not found, find cheapest in same category
    3. If no category match, mark as not found
    """
    all_deals = storage.get_active_deals().get("deals", [])
    
    if not all_deals:
        return {
            "optimization": [],
            "not_found": items,
            "recommendation": "No deals available right now."
        }
    
    stores = set(d.get('store', 'Unknown') for d in all_deals)
    found_items = set()
    baskets = {}
    not_found = []
    alternatives = []  # Category-based suggestions
    
    for item in items:
        item_category = guess_category(item)
        best_match = None
        best_store = None
        match_type = None  # "exact" or "category"
        
        # Step 1: Try to find exact match across all stores
        for store in stores:
            store_deals = [d for d in all_deals if d.get('store') == store]
            matches = find_product_matches(item, store_deals, threshold=0.6)
            
            if matches:
                # Found exact match
                candidate = matches[0]
                if not best_match or float(candidate.get('price', 99)) < float(best_match.get('price', 99)):
                    best_match = candidate
                    best_store = store
                    match_type = "exact"
        
        # Step 2: If no exact match, find cheapest in same category
        if not best_match and item_category != "Other":
            category_deals = [d for d in all_deals if d.get('category') == item_category]
            if category_deals:
                # Sort by unit price
                category_deals.sort(key=lambda d: parse_unit_price(d))
                best_category = category_deals[0]
                alternatives.append({
                    "original_item": item,
                    "suggestion": best_category.get('product_name'),
                    "price": best_category.get('price'),
                    "store": best_category.get('store'),
                    "reason": f"Cheapest {item_category} this week"
                })
        
        # Record result
        if best_match and best_store:
            found_items.add(item)
            if best_store not in baskets:
                baskets[best_store] = {"matches": [], "total_price": 0.0}
            baskets[best_store]["matches"].append({
                "item": item,
                "product": best_match.get('product_name'),
                "price": float(best_match.get('price', 0))
            })
            baskets[best_store]["total_price"] += float(best_match.get('price', 0))
        else:
            if item not in [a["original_item"] for a in alternatives]:
                not_found.append(item)
    
    # Format results
    results = []
    for store, data in baskets.items():
        results.append({
            "store": store,
            "match_count": len(data["matches"]),
            "total_price": round(data["total_price"], 2),
            "matches": data["matches"]
        })
    
    results.sort(key=lambda x: (-x['match_count'], x['total_price']))
    
    # Smart recommendation
    recommendation = ""
    if results:
        best = results[0]
        if best["match_count"] == len(items):
            recommendation = f"✅ {best['store']} has all {len(items)} items! Total: €{best['total_price']}"
        else:
            recommendation = f"🏆 {best['store']} has {best['match_count']}/{len(items)} items."
    
    if alternatives:
        recommendation += f" 💡 {len(alternatives)} category alternatives found."
    
    if not_found:
        recommendation += f" ❌ {len(not_found)} items not available this week."
    
    return {
        "optimization": results,
        "alternatives": alternatives,
        "not_found": not_found,
        "found_count": len(found_items),
        "total_items": len(items),
        "recommendation": recommendation
    }
