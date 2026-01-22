from db import db
import json
from typing import List, Dict, Optional

def get_api_key() -> Optional[str]:
    result = db.execute_query("SELECT api_key FROM users WHERE unique_id = 'default_user'")
    return result[0]['api_key'] if result and result[0]['api_key'] else None

def save_api_key(key: str):
    db.execute_query("UPDATE users SET api_key = %s WHERE unique_id = 'default_user'", (key,))

def save_active_deals(deals: List[Dict], store_name: str = "Unknown Store", upload_id: int = None):
    # Depending on how 'active deals' are defined. 
    # For now, we just insert them into the deals table linked to an upload.
    # Note: caller should provide upload_id
    
    for deal in deals:
        # Clean price for Decimal
        price_str = deal.get('price', '0').replace('€', '').replace(',', '.')
        try:
            price = float(price_str)
        except:
            price = 0.0

        db.execute_query(
            """
            INSERT INTO deals (upload_id, product_name, price, original_price, unit, store, confidence, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                upload_id,
                deal.get('product_name'),
                price,
                deal.get('original_price'),
                deal.get('unit'),
                store_name,
                deal.get('confidence', 0.95),
                deal.get('source', 'gemini')
            )
        )

def get_active_deals() -> Dict:
    # Retrieve deals from the most recent upload(s) or just all recent deals
    # Let's get deals from the last 7 days
    results = db.execute_query(
        """
        SELECT product_name, price, original_price, unit, store, confidence, source, created_at 
        FROM deals 
        ORDER BY created_at DESC 
        LIMIT 50
        """
    )
    # Format for frontend
    formatted = []
    for r in results:
        formatted.append({
            "product_name": r['product_name'],
            "price": str(r['price']), # Convert Decimal to string
            "original_price": r['original_price'],
            "unit": r['unit'],
            "store": r['store'],
            "created_at": str(r['created_at'])
        })
    return {"deals": formatted, "count": len(formatted)}

def get_shopping_list() -> List[str]:
    results = db.execute_query("SELECT item FROM shopping_list ORDER BY created_at DESC")
    return [r['item'] for r in results]

def add_to_list(item: str):
    try:
        db.execute_query("INSERT INTO shopping_list (item) VALUES (%s)", (item,))
    except Exception:
        pass # Ignore duplicates

def remove_from_list(item: str):
    db.execute_query("DELETE FROM shopping_list WHERE item = %s", (item,))

def get_watchlist() -> List[str]:
    results = db.execute_query("SELECT item FROM watchlist ORDER BY created_at DESC")
    return [r['item'] for r in results]

def add_watchlist_item(item: str):
    try:
        db.execute_query("INSERT INTO watchlist (item) VALUES (%s)", (item,))
    except Exception:
        pass

def remove_watchlist_item(item: str):
    db.execute_query("DELETE FROM watchlist WHERE item = %s", (item,))

def log_upload(filename: str, deal_count: int, file_path: str, file_hash: str) -> int:
    upload_id = db.execute_query(
        "INSERT INTO uploads (filename, file_hash, file_path, deal_count) VALUES (%s, %s, %s, %s)",
        (filename, file_hash, file_path, deal_count)
    )
    return upload_id

def get_upload_history() -> List[Dict]:
    results = db.execute_query("SELECT * FROM uploads ORDER BY timestamp DESC")
    for r in results:
        r['timestamp'] = str(r['timestamp'])
    return results

def reset_user_data():
    db.execute_query("TRUNCATE TABLE shopping_list")
    db.execute_query("TRUNCATE TABLE deals")
    db.execute_query("TRUNCATE TABLE uploads") 
    # Keep watchlist and settings? Or clear all? 
    # User said "Reset All Data" usually means transactional data.
    # We will keep settings (API Key).
