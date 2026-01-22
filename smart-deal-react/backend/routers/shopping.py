from fastapi import APIRouter, HTTPException, Body
from services import storage
from typing import List, Dict
import logging

router = APIRouter(prefix="/api/shopping-list", tags=["shopping"])

@router.get("/")
def get_list():
    return storage.get_shopping_list()

@router.post("/")
def add_item(item: dict = Body(...)):
    # item = {"item": "Milk"}
    storage.add_to_list(item.get("item"))
    return {"status": "ok", "list": storage.get_shopping_list()}

@router.delete("/{item_name}")
def delete_item(item_name: str):
    storage.remove_from_list(item_name)
    return {"status": "ok", "list": storage.get_shopping_list()}

@router.post("/optimize")
def optimize_list(items: List[str] = Body(..., embed=True)):
    """
    Finds the cheapest store for the given list of items.
    """
    # 1. Get keywords from items (e.g. "Milk" -> "Milk")
    # 2. Query active deals for each item
    # 3. Simple Algorithm:
    #    - Create a basket for each store.
    #    - If store has item, add price.
    #    - Return store with most matches and lowest price.
    
    recommendations = []
    
    # Simple fuzzy match logic (could be moved to storage service)
    # Get all active deals first to avoid N+1 queries
    all_deals_data = storage.get_active_deals() # returns {"deals": [...]}
    all_deals = all_deals_data.get("deals", [])
    
    # Store baskets: { "Rewe": { "matches": ["Milk", "Eggs"], "total": 2.50 } }
    baskets = {}

    for item in items:
        item_lower = item.lower()
        found_match = False
        
        # Find best deal for this item across all deals
        # Sort deals by price to find cheapest first
        # Note: deals price is string "0.99", need float for comparison
        
        # Filter relevant deals
        relevant_deals = [
            d for d in all_deals 
            if item_lower in d['product_name'].lower() 
            or d['product_name'].lower() in item_lower
        ]
        
        if not relevant_deals:
            continue
            
        # Find cheapest among relevant
        # Cast price string to float
        for d in relevant_deals:
            try:
                price = float(d['price'])
            except:
                price = 999.0
            d['_price_float'] = price

        relevant_deals.sort(key=lambda x: x['_price_float'])
        best_deal = relevant_deals[0]
        
        # Add to store basket
        store = best_deal['store']
        if store not in baskets:
            baskets[store] = {"matches": [], "total": 0.0, "deal_count": 0}
            
        baskets[store]["matches"].append({
            "item": item,
            "product": best_deal['product_name'],
            "price": best_deal['_price_float']
        })
        baskets[store]["total"] += best_deal['_price_float']
        baskets[store]["deal_count"] += 1

    # Format result
    # Convert dict to list
    results = []
    for store, data in baskets.items():
        results.append({
            "store": store,
            "match_count": data["deal_count"],
            "total_price": round(data["total"], 2),
            "matches": data["matches"]
        })
    
    # Sort by number of matches (desc) then price (asc)
    results.sort(key=lambda x: (-x['match_count'], x['total_price']))
    
    return {"optimization": results}
