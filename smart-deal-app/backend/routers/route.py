"""
Route Planning API for Smart Shopping Route Optimizer.
Uses same category-based smart matching as optimization.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel
from services import storage
from services.rag_service import find_product_matches
import math
import re

router = APIRouter(prefix="/api/route", tags=["route"])

# Category keywords (same as shopping.py)
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
    item_lower = item.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in item_lower:
                return category
    return "Other"

def parse_unit_price(deal: Dict) -> float:
    try:
        price = float(deal.get('price', 0))
        unit = deal.get('unit', '').lower()
        if 'kg' in unit:
            return price
        elif 'g' in unit:
            match = re.search(r'(\d+)\s*g', unit)
            if match:
                grams = int(match.group(1))
                return (price / grams) * 1000
        return price
    except:
        return 999.0

class StoreLocation(BaseModel):
    name: str
    type: Optional[str] = "Supermarket"
    lat: float
    lng: float

class RoutePlanRequest(BaseModel):
    items: List[str]
    location: List[float]
    max_distance_km: float = 5.0
    available_stores: List[StoreLocation] = []

class AlternativeRequest(BaseModel):
    item: str
    category: Optional[str] = None
    excluded_stores: List[str] = []

class RouteConfirmRequest(BaseModel):
    selected_stores: List[str]
    substitutions: List[Dict] = []

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@router.post("/plan")
async def plan_route(request: RoutePlanRequest):
    """Smart route planning with category-based matching."""
    items = request.items
    user_lat, user_lng = request.location
    max_distance = request.max_distance_km
    available_stores = request.available_stores
    
    if not items:
        raise HTTPException(400, "No items in cart")
    
    all_deals = storage.get_active_deals().get("deals", [])
    
    if not all_deals:
        return {
            "status": "no_deals",
            "message": "No deals available.",
            "recommended_stores": [],
            "items_not_found": items,
            "alternatives": []
        }
    
    # Group deals by store
    stores_deals = {}
    for deal in all_deals:
        store = deal.get('store', 'Unknown')
        if store not in stores_deals:
            stores_deals[store] = []
        stores_deals[store].append(deal)
    
    store_results = []
    all_found_items = set()
    category_alternatives = []
    
    for store_name, deals in stores_deals.items():
        # Find store distance
        distance = 999.0
        store_loc = None
        
        for s in available_stores:
            if s.name.lower() in store_name.lower() or store_name.lower() in s.name.lower() or (s.type and s.type.lower() in store_name.lower()):
                dist = haversine_distance(user_lat, user_lng, s.lat, s.lng)
                if dist < distance:
                    distance = dist
                    store_loc = s
        
        if distance > max_distance:
            continue
        
        # Match items with 0.6 threshold (strict)
        matches = []
        total_price = 0.0
        
        for item in items:
            product_matches = find_product_matches(item, deals, threshold=0.6)
            
            if product_matches:
                best = product_matches[0]
                price = float(best.get('price', 0))
                matches.append({
                    "item": item,
                    "product": best.get('product_name'),
                    "price": price,
                    "match_type": "exact"
                })
                total_price += price
                all_found_items.add(item)
        
        if matches:
            result = {
                "store": store_name,
                "match_count": len(matches),
                "total_price": round(total_price, 2),
                "distance_km": round(distance, 1),
                "matches": matches,
                "worthwhile": len(matches) >= 2 or len(matches) == len(items),
                "score": len(matches) * 10 - distance
            }
            if store_loc:
                result["lat"] = store_loc.lat
                result["lng"] = store_loc.lng
            store_results.append(result)
    
    # Category fallback for not-found items
    not_found = [item for item in items if item not in all_found_items]
    
    for item in not_found:
        item_category = guess_category(item)
        if item_category == "Other":
            continue
            
        category_deals = [d for d in all_deals if d.get('category') == item_category]
        if category_deals:
            category_deals.sort(key=lambda d: parse_unit_price(d))
            best = category_deals[0]
            category_alternatives.append({
                "original_item": item,
                "suggestion": best.get('product_name'),
                "price": best.get('price'),
                "store": best.get('store'),
                "reason": f"Cheapest {item_category}"
            })
    
    # Sort stores by score
    store_results.sort(key=lambda x: -x['score'])
    
    recommended = [s for s in store_results if s['worthwhile']]
    not_recommended = [s for s in store_results if not s['worthwhile']]
    
    # Route order (simple greedy)
    route_order = []
    if recommended:
        remaining = recommended.copy()
        curr_lat, curr_lng = user_lat, user_lng
        while remaining:
            def dist_to(s):
                return haversine_distance(curr_lat, curr_lng, s.get('lat', user_lat), s.get('lng', user_lng))
            nearest = min(remaining, key=dist_to)
            route_order.append(nearest['store'])
            remaining.remove(nearest)
            curr_lat = nearest.get('lat', curr_lat)
            curr_lng = nearest.get('lng', curr_lng)
    
    # Smart recommendation
    recommendation = ""
    if recommended:
        best = recommended[0]
        recommendation = f"🏆 Start at {best['store']} ({best['match_count']} items, {best['distance_km']}km away)"
    if category_alternatives:
        recommendation += f" | 💡 {len(category_alternatives)} alternatives available"
    if not_found and not category_alternatives:
        recommendation += f" | ❌ {len(not_found)} items not found this week"
    
    return {
        "status": "success",
        "recommended_stores": recommended,
        "not_recommended": not_recommended,
        "route_order": route_order,
        "total_items_found": len(all_found_items),
        "items_not_found": [i for i in not_found if i not in [a['original_item'] for a in category_alternatives]],
        "alternatives": category_alternatives,
        "recommendation": recommendation
    }

@router.post("/alternatives")
async def get_alternatives(request: AlternativeRequest):
    """Find alternative products using category matching."""
    item = request.item
    excluded_stores = request.excluded_stores
    
    all_deals = storage.get_active_deals().get("deals", [])
    item_category = guess_category(item)
    
    # Same product at other stores
    same_product = []
    for deal in all_deals:
        if deal.get('store') in excluded_stores:
            continue
        matches = find_product_matches(item, [deal], threshold=0.6)
        if matches:
            same_product.append(matches[0])
    
    # Same category alternatives
    same_category = []
    if item_category != "Other":
        category_deals = [d for d in all_deals 
                         if d.get('category') == item_category 
                         and d.get('store') not in excluded_stores]
        category_deals.sort(key=lambda d: parse_unit_price(d))
        same_category = category_deals[:5]
    
    return {
        "item": item,
        "category": item_category,
        "same_product_alternatives": same_product[:5],
        "same_category_alternatives": same_category,
        "total_alternatives": len(same_product) + len(same_category)
    }

@router.post("/confirm")
async def confirm_route(request: RouteConfirmRequest):
    """Confirm route and apply substitutions."""
    for sub in request.substitutions:
        original = sub.get('original')
        replacement = sub.get('replacement')
        if original and replacement:
            try:
                storage.remove_from_list(original)
                storage.add_to_list(replacement)
            except:
                pass
    
    return {
        "status": "confirmed",
        "selected_stores": request.selected_stores,
        "substitutions_applied": len(request.substitutions),
        "message": f"Route confirmed! Visit {len(request.selected_stores)} store(s)."
    }
