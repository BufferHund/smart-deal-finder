"""
RAG-like service for product matching and alternative recommendations.
Uses fuzzy matching and category-based retrieval to find relevant deals.
"""
from typing import List, Dict, Optional, Tuple
from db import db
import re
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, remove special chars"""
    return re.sub(r'[^a-zäöüß0-9\s]', '', text.lower().strip())

def similarity_score(a: str, b: str) -> float:
    """Calculate similarity between two strings (0-1)"""
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def find_product_matches(item: str, deals: List[Dict], threshold: float = 0.4) -> List[Dict]:
    """
    Find deals matching a shopping list item using fuzzy matching.
    Returns list of matches sorted by relevance score.
    """
    item_normalized = normalize_text(item)
    matches = []
    
    for deal in deals:
        product_name = deal.get('product_name', '')
        product_normalized = normalize_text(product_name)
        
        # Calculate match score
        score = 0.0
        
        # Exact substring match (high score)
        if item_normalized in product_normalized or product_normalized in item_normalized:
            score = 0.9
        else:
            # Fuzzy similarity
            score = similarity_score(item, product_name)
        
        # Boost score if category matches common keywords
        if score >= threshold:
            matches.append({
                **deal,
                '_match_score': score,
                '_matched_item': item
            })
    
    # Sort by score descending, then by price ascending
    matches.sort(key=lambda x: (-x['_match_score'], float(x.get('price', 999))))
    return matches

def find_alternatives(
    item: str,
    category: str,
    excluded_stores: List[str],
    all_deals: List[Dict],
    limit: int = 5
) -> List[Dict]:
    """
    Find alternative products at non-excluded stores.
    Strategy:
    1. Same product at different stores
    2. Same category products at nearby stores
    """
    alternatives = []
    item_normalized = normalize_text(item)
    
    for deal in all_deals:
        store = deal.get('store', '')
        if store in excluded_stores:
            continue
            
        product_name = deal.get('product_name', '')
        deal_category = deal.get('category', '')
        
        # Check if same/similar product
        score = similarity_score(item, product_name)
        if score >= 0.5:
            alternatives.append({
                **deal,
                '_alt_type': 'same_product',
                '_similarity': score
            })
        # Check if same category
        elif category and deal_category and normalize_text(category) in normalize_text(deal_category):
            alternatives.append({
                **deal,
                '_alt_type': 'same_category',
                '_similarity': 0.3
            })
    
    # Sort by similarity and limit
    alternatives.sort(key=lambda x: -x['_similarity'])
    return alternatives[:limit]

def calculate_store_value(
    store: str,
    matches: List[Dict],
    distance_km: float,
    min_distance: float = 0.5
) -> Dict:
    """
    Calculate value score for visiting a store.
    Formula: score = (total_savings * match_count) / (distance + min_distance)
    
    Higher score = more worthwhile to visit
    """
    if not matches:
        return {
            'store': store,
            'score': 0,
            'match_count': 0,
            'total_savings': 0,
            'distance_km': distance_km,
            'worthwhile': False,
            'reason': 'No matching products'
        }
    
    total_savings = 0.0
    for m in matches:
        try:
            price = float(m.get('price', 0))
            original = m.get('original_price', '')
            if original:
                orig_price = float(str(original).replace('€', '').replace(',', '.'))
                total_savings += max(0, orig_price - price)
            else:
                # Assume 20% savings if no original price
                total_savings += price * 0.2
        except:
            pass
    
    match_count = len(matches)
    score = (total_savings * match_count) / (distance_km + min_distance)
    
    # Determine if worthwhile
    # Rule: Not worthwhile if only 1 item AND distance > 1km AND savings < 2€
    worthwhile = True
    reason = ''
    
    if match_count == 1 and distance_km > 1.0 and total_savings < 2.0:
        worthwhile = False
        reason = f"Only 1 item, {distance_km:.1f}km away, saves only €{total_savings:.2f}"
    elif match_count == 1 and distance_km > 2.0:
        worthwhile = False
        reason = f"Only 1 item and {distance_km:.1f}km away"
    
    return {
        'store': store,
        'score': round(score, 2),
        'match_count': match_count,
        'total_savings': round(total_savings, 2),
        'distance_km': distance_km,
        'worthwhile': worthwhile,
        'reason': reason,
        'matches': matches
    }

def get_deals_by_store(store_name: str) -> List[Dict]:
    """Get all deals for a specific store"""
    results = db.execute_query(
        """
        SELECT product_name, price, original_price, unit, store, category, image_url
        FROM deals 
        WHERE LOWER(store) LIKE %s
        ORDER BY created_at DESC
        LIMIT 100
        """,
        (f"%{store_name.lower()}%",)
    )
    return [dict(r) for r in results] if results else []

def get_deals_by_category(category: str) -> List[Dict]:
    """Get all deals for a specific category"""
    results = db.execute_query(
        """
        SELECT product_name, price, original_price, unit, store, category, image_url
        FROM deals 
        WHERE LOWER(category) LIKE %s
        ORDER BY price ASC
        LIMIT 50
        """,
        (f"%{category.lower()}%",)
    )
    return [dict(r) for r in results] if results else []
