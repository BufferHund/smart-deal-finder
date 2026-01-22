from db import db
import json
from typing import List, Dict, Optional

def get_api_key() -> Optional[str]:
    result = db.execute_query("SELECT api_key FROM users WHERE unique_id = 'default_user'")
    return result[0]['api_key'] if result and result[0]['api_key'] else None

def save_api_key(key: str):
    db.execute_query("UPDATE users SET api_key = %s WHERE unique_id = 'default_user'", (key,))

def save_active_deals(deals: List[Dict], store_name: str = "Unknown Store", upload_id: int = None, visibility: str = 'public'):
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
            INSERT INTO deals (upload_id, product_name, price, original_price, unit, store, confidence, source, category, image_url, visibility)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                upload_id,
                deal.get('product_name'),
                price,
                deal.get('original_price'),
                deal.get('unit'),
                store_name,
                deal.get('confidence', 0.95),
                deal.get('source', 'gemini'),
                deal.get('category', 'Uncategorized'),
                deal.get('image_url'),
                visibility
            )
        )

def get_active_deals() -> Dict:
    # Retrieve deals from the most recent upload(s) or just all recent deals
    # Let's get deals from the last 7 days
    # Filtering: Return Public OR Private (since we assume single user for now, private is fine to return)
    # In a real multi-user app, this would be: WHERE visibility = 'public' OR (visibility = 'private' AND user_id = current_user)
    results = db.execute_query(
        """
        SELECT product_name, price, original_price, unit, store, confidence, source, category, image_url, created_at, visibility
        FROM deals 
        ORDER BY created_at DESC 
        LIMIT 100
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
            "source": r.get('source', 'gemini'),
            "category": r['category'],
            "image_url": r['image_url'],
            "visibility": r.get('visibility', 'public'),
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

def log_upload(filename: str, deal_count: int, file_path: str, file_hash: str, visibility: str = 'public') -> int:
    upload_id = db.execute_query(
        "INSERT INTO uploads (filename, file_hash, file_path, deal_count, visibility) VALUES (%s, %s, %s, %s, %s)",
        (filename, file_hash, file_path, deal_count, visibility)
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
    # Keep watchlist and settings? Or clear all? 
    # User said "Reset All Data" usually means transactional data.
    # We will keep settings (API Key).

# Wallet / Loyalty Cards
def get_cards() -> List[Dict]:
    results = db.execute_query("SELECT * FROM loyalty_cards ORDER BY created_at DESC")
    for r in results:
        r['created_at'] = str(r['created_at'])
    return results

def add_card(store_name: str, card_number: str, card_format: str = "BARCODE", image_path: Optional[str] = None):
    # Assign a random color for UI if no logic provided yet
    import random
    colors = ["bg-red-500", "bg-blue-500", "bg-green-500", "bg-yellow-500", "bg-purple-500", "bg-pink-500"]
    color = random.choice(colors)
    
    db.execute_query(
        "INSERT INTO loyalty_cards (store_name, card_number, card_format, image_path, color) VALUES (%s, %s, %s, %s, %s)",
        (store_name, card_number, card_format, image_path, color)
    )

def delete_card(card_id: int):
    db.execute_query("DELETE FROM loyalty_cards WHERE id = %s", (card_id,))

# Receipts
def add_receipt(store_name: str, total: float, date: str, image_path: str, items: List[str]):
    # items is a list, save as JSON
    items_json = json.dumps(items)
    db.execute_query(
        "INSERT INTO receipts (store_name, total_amount, purchase_date, image_path, items) VALUES (%s, %s, %s, %s, %s)",
        (store_name, total, date, image_path, items_json)
    )

def get_receipts() -> List[Dict]:
    results = db.execute_query("SELECT * FROM receipts ORDER BY purchase_date DESC")
    for r in results:
        r['total_amount'] = str(r['total_amount'])
        r['purchase_date'] = str(r['purchase_date'])
        r['created_at'] = str(r['created_at'])
        if r['items']:
             try:
                 r['items'] = json.loads(r['items'])
             except:
                 r['items'] = []
    return results

def delete_receipt(receipt_id: int):
    db.execute_query("DELETE FROM receipts WHERE id = %s", (receipt_id,))

def get_ai_token() -> Optional[str]:
    """
    Retrieves a valid AI token for API calls.
    Prioritizes user's own API key, then falls back to rate-limited trial token.
    """
    from datetime import date
    
    # 1. Check if user has their own key
    user_key = get_api_key()
    if user_key:
        return user_key
    
    # 2. Try trial token with rate limiting
    today = date.today().isoformat()
    
    # Get any active trial token
    token_data = db.execute_query(
        "SELECT * FROM app_tokens WHERE is_active = TRUE AND token_type = 'trial' LIMIT 1"
    )
    
    if not token_data:
        return None
    
    token_row = token_data[0]
    token = token_row['token']
    usage_count = token_row['usage_count'] or 0
    last_used_date = str(token_row['last_used_date']) if token_row['last_used_date'] else None
    max_limit = token_row['max_daily_limit'] or 1000
    
    # Reset count if it's a new day
    if last_used_date != today:
        usage_count = 0
        db.execute_query(
            "UPDATE app_tokens SET usage_count = 0, last_used_date = %s WHERE id = %s",
            (today, token_row['id'])
        )
    
    # Check limit
    if usage_count >= max_limit:
        return None  # Rate limit exceeded
    
    # Increment usage
    db.execute_query(
        "UPDATE app_tokens SET usage_count = usage_count + 1, last_used_date = %s WHERE id = %s",
        (today, token_row['id'])
    )
    
    return token

# User Settings
def get_user_settings():
    res = db.execute_query("SELECT settings FROM users WHERE unique_id = 'default_user'")
    if res and res[0]['settings']:
        return json.loads(res[0]['settings'])
    return {}

def update_user_settings(settings: Dict):
    current = get_user_settings()
    current.update(settings)
    db.execute_query("UPDATE users SET settings = %s WHERE unique_id = 'default_user'", (json.dumps(current),))


def get_spending_stats() -> Dict:
    # Aggregate receipts by month
    receipts = get_receipts()
    from collections import defaultdict
    from datetime import datetime
    
    monthly_spend = defaultdict(float)
    
    for r in receipts:
        try:
            # date format might be YYYY-MM-DD or similar string
            date_str = str(r['purchase_date']).split(' ')[0] # Handle datetime string
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            month_key = dt.strftime('%b') # Jan, Feb...
            monthly_spend[month_key] += float(r['total_amount'])
        except Exception as e:
            print(f"Error parsing receipt date/total: {e}")
            continue
            
    # Ensure we have some data even if empty
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []
    for m in months:
        data.append({"name": m, "value": monthly_spend.get(m, 0.0)})
        
    # Current month total
    current_month = datetime.now().strftime('%b')
    current_total = monthly_spend.get(current_month, 0.0)
    
    # Gamification Logic
    upload_count = len(get_upload_history())
    receipt_count = len(receipts)
    
    # Points Strategy: 50 pts per receipt, 20 pts per upload
    points = (receipt_count * 50) + (upload_count * 20)
    
    # Level Strategy: Every 1000 points is a level
    level = int(points / 1000) + 1
    level_progress = (points % 1000) / 10  # 0 to 100%
    
    # Badges
    badges = []
    if receipt_count >= 1:
        badges.append("First Scan")
    if upload_count >= 1:
        badges.append("Deal Hunter")
    if points >= 500:
        badges.append("Saver Scout")
    if points >= 2000:
        badges.append("Budget Master")
        
    # Mock saved amount (10% of total spent for now, until we extract real savings)
    total_spent_lifetime = sum(float(r['total_amount']) for r in receipts)
    total_saved = total_spent_lifetime * 0.12 

    return {
        "chart_data": data,
        "current_month_total": current_total,
        "total_receipts": len(receipts),
        "gamification": {
            "points": points,
            "level": level,
            "level_progress": level_progress,
            "badges": badges,
            "total_saved": total_saved
        }
    }
