"""
Route Planning API for Smart Shopping Route Optimizer.
Provides endpoints for planning optimized shopping routes based on cart items and location.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel
from services import storage
from services.rag_service import (
    find_product_matches,
    find_alternatives,
    calculate_store_value
)
import math

router = APIRouter(prefix="/api/route", tags=["route"])

class RoutePlanRequest(BaseModel):
    items: List[str]
    location: List[float]  # [lat, lng]
    max_distance_km: float = 5.0

class AlternativeRequest(BaseModel):
    item: str
    category: Optional[str] = None
    excluded_stores: List[str] = []

class RouteConfirmRequest(BaseModel):
    selected_stores: List[str]
    substitutions: List[Dict] = []  # [{original: str, replacement: str, store: str}]

# German supermarket locations (mock data - in production would use Overpass API)
STORE_LOCATIONS = {
    "Rewe": {"lat": 52.5200, "lng": 13.4050},
    "Lidl": {"lat": 52.5180, "lng": 13.4100},
    "Aldi": {"lat": 52.5220, "lng": 13.4000},
    "Edeka": {"lat": 52.5150, "lng": 13.4150},
    "Penny": {"lat": 52.5250, "lng": 13.3950},
    "Netto": {"lat": 52.5100, "lng": 13.4200},
    "Kaufland": {"lat": 52.5300, "lng": 13.3900},
}

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_store_distance(store_name: str, user_lat: float, user_lng: float) -> float:
    """Get distance to a store from user location"""
    # Try to find store in our location map
    for key, coords in STORE_LOCATIONS.items():
        if key.lower() in store_name.lower():
            return haversine_distance(user_lat, user_lng, coords["lat"], coords["lng"])
    # Default distance if store not found
    return 2.0

@router.post("/plan")
async def plan_route(request: RoutePlanRequest):
    """
    Generate an optimized shopping route based on cart items and user location.
    
    Returns:
    - recommended_stores: Stores worth visiting with their matches
    - not_recommended: Stores not worth the trip (with reasons)
    - total_savings: Estimated total savings
    - route_order: Optimized order to visit stores (TSP-like)
    """
    items = request.items
    user_lat, user_lng = request.location
    max_distance = request.max_distance_km
    
    if not items:
        raise HTTPException(status_code=400, detail="No items in cart")
    
    # Get all active deals
    deals_data = storage.get_active_deals()
    all_deals = deals_data.get("deals", [])
    
    if not all_deals:
        return {
            "status": "no_deals",
            "message": "No deals available. Please upload some brochures first.",
            "recommended_stores": [],
            "not_recommended": [],
            "total_savings": 0
        }
    
    # Group deals by store
    stores_deals = {}
    for deal in all_deals:
        store = deal.get('store', 'Unknown')
        if store not in stores_deals:
            stores_deals[store] = []
        stores_deals[store].append(deal)
    
    # For each store, find matching products and calculate value
    store_results = []
    
    for store, deals in stores_deals.items():
        # Calculate distance
        distance = get_store_distance(store, user_lat, user_lng)
        if distance > max_distance:
            continue
        
        # Find matches for all items at this store
        all_matches = []
        matched_items = set()
        
        for item in items:
            matches = find_product_matches(item, deals, threshold=0.4)
            if matches:
                # Take best match for each item
                best = matches[0]
                if best['_matched_item'] not in matched_items:
                    all_matches.append(best)
                    matched_items.add(best['_matched_item'])
        
        # Calculate store value
        value = calculate_store_value(store, all_matches, distance)
        
        # Add coordinates
        coords = STORE_LOCATIONS.get(store, {})
        if not coords:
             # Try Partial Match
             for k, v in STORE_LOCATIONS.items():
                 if k.lower() in store.lower():
                     coords = v
                     break
        
        value['lat'] = coords.get('lat', 0.0)
        value['lng'] = coords.get('lng', 0.0)
        
        store_results.append(value)
    
    # Separate into recommended and not recommended
    recommended = [s for s in store_results if s['worthwhile']]
    not_recommended = [s for s in store_results if not s['worthwhile']]
    
    # Sort recommended by score
    recommended.sort(key=lambda x: -x['score'])
    
    # Optimize route order (simple greedy TSP)
    if len(recommended) > 1:
        route_order = optimize_route_order(recommended, user_lat, user_lng)
    else:
        route_order = [s['store'] for s in recommended]
    
    # Calculate totals
    total_savings = sum(s['total_savings'] for s in recommended)
    total_items = sum(s['match_count'] for s in recommended)
    
    return {
        "status": "success",
        "recommended_stores": recommended,
        "not_recommended": not_recommended,
        "route_order": route_order,
        "total_savings": round(total_savings, 2),
        "total_items_found": total_items,
        "items_not_found": [i for i in items if not any(
            i in str(s.get('matches', [])) for s in recommended
        )]
    }

def optimize_route_order(stores: List[Dict], start_lat: float, start_lng: float) -> List[str]:
    """
    Simple greedy TSP: Start from user, always go to nearest unvisited store.
    """
    remaining = stores.copy()
    order = []
    current_lat, current_lng = start_lat, start_lng
    
    while remaining:
        # Find nearest store
        nearest = min(remaining, key=lambda s: get_store_distance(s['store'], current_lat, current_lng))
        order.append(nearest['store'])
        remaining.remove(nearest)
        # Update current position
        store_coords = STORE_LOCATIONS.get(nearest['store'], {"lat": current_lat, "lng": current_lng})
        current_lat, current_lng = store_coords.get("lat", current_lat), store_coords.get("lng", current_lng)
    
    return order

@router.post("/alternatives")
async def get_alternatives(request: AlternativeRequest):
    """
    Find alternative products for an item, excluding certain stores.
    
    Returns alternatives sorted by:
    1. Same product at different stores
    2. Same category products
    """
    item = request.item
    category = request.category
    excluded_stores = request.excluded_stores
    
    # Get all deals
    deals_data = storage.get_active_deals()
    all_deals = deals_data.get("deals", [])
    
    alternatives = find_alternatives(item, category, excluded_stores, all_deals, limit=10)
    
    # Group by type
    same_product = [a for a in alternatives if a.get('_alt_type') == 'same_product']
    same_category = [a for a in alternatives if a.get('_alt_type') == 'same_category']
    
    return {
        "item": item,
        "same_product_alternatives": same_product,
        "same_category_alternatives": same_category,
        "total_alternatives": len(alternatives)
    }

@router.post("/confirm")
async def confirm_route(request: RouteConfirmRequest):
    """
    Confirm the selected route and apply any substitutions to the shopping list.
    """
    selected_stores = request.selected_stores
    substitutions = request.substitutions
    
    # Apply substitutions to shopping list
    for sub in substitutions:
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
        "selected_stores": selected_stores,
        "substitutions_applied": len(substitutions),
        "message": f"Route confirmed! Visit {len(selected_stores)} store(s)."
    }
