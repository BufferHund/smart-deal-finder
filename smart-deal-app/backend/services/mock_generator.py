import random
from services import storage
from db import db
from datetime import datetime, timedelta

STORES = ["Rewe", "Lidl", "Aldi Süd", "Aldi Nord", "Edeka", "Netto Marken-Discount", "Penny", "Kaufland", "dm", "Rossmann"]

CATEGORIES = {
    "Fruit & Veg": [
        "Bio Bananen", "Äpfel Elstar", "Gurken", "Tomaten Rispen", "Kartoffeln vorwiegend festkochend", 
        "Paprika Mix", "Weintrauben hell", "Zucchini", "Brokkoli", "Champignons braun"
    ],
    "Meat & Fish": [
        "Rinderhackfleisch", "Hähnchenbrustfilet", "Schweineschnitzel", "Lachsfilet", "Thunfischdose", 
        "Bio Rindersteak", "Gemischtes Hackfleisch", "Bratwurst", "Salami Aufschnitt", "Kochschinken"
    ],
    "Dairy": [
        "Weihenstephan H-Milch", "Müller Milchreis", "Kerrygold Butter", "Philadelphia Frischkäse", 
        "Landliebe Joghurt", "Exquisa Quark", "Alpro Soya", "Gouda Jung", "Mozzarella", "Schlagsahne"
    ],
    "Bakery": [
        "Harry Toast", "Brezel", "Baguette", "Vollkornbrot", "Kaiserbrötchen", "Croissant", 
        "Golden Toast", "Lieken Urkorn", "Ciabatta", "Laugenstange"
    ],
    "Drinks": [
        "Coca-Cola", "Fanta", "Paulaner Spezi", "Volvic Wasser", "Gerolsteiner Sprudel", 
        "Red Bull", "Orangensaft Hohes C", "Krombacher Pils", "Augustiner Helles", "Rotkäppchen Sekt"
    ],
    "Snacks": [
        "Haribo Goldbären", "Milka Alpenmilch", "Ritter Sport", "Lay's Chips", "Pringles", 
        "Leibniz Butterkeks", "Nutella", "Kinder Schokolade", "Chio Chips", "NicNac's"
    ],
    "Pantry": [
        "Barilla Spaghetti", "Knorr Fix", "Maggi Würze", "Dr. Oetker Pudding", "Olivenöl", 
        "Mehl Type 405", "Zucker", "Heinz Ketchup", "Thomy Mayonnaise", "Reis"
    ],
    "Household": [
        "Persil Waschmittel", "Frosch Reiniger", "Pril Spülmittel", "Zewa Toilettenpapier", 
        "Ariel Pods", "Somat Tabs", "Tempo Taschentücher", "Nivea Duschgel", "Dove Deo", "Colgate Zahnpasta"
    ]
}

UNITS = ["500g", "1kg", "100g", "1.5L", "1L", "0.75L", "Packung", "Stück", "250g", "200g"]

def generate_price():
    # Generate psychological prices: x.99, x.49, x.29
    base = random.randint(0, 15)
    decimal = random.choice([99, 49, 29, 79, 19])
    return f"{base}.{decimal}" if base > 0 else f"0.{decimal}"

def generate_mock_data(count=2000):
    print(f"Generating {count} mock deals...")
    deals = []
    
    # 1. Clear existing deals? Optional, but maybe safer for "Demo Mode" to wipe slate or just append.
    # Let's just append for now, user can use "Reset" button if they want clean slate.
    
    # 2. Generate
    start_date = datetime.now()
    
    for _ in range(count):
        category = random.choice(list(CATEGORIES.keys()))
        product = random.choice(CATEGORIES[category])
        store = random.choice(STORES)
        
        # Add random "Bio" or Brand prefix sometimes if not present
        if random.random() > 0.8 and "Bio" not in product:
             product = f"Bio {product}"
             
        original_price = generate_price()
        # Discount logic
        price_float = float(original_price)
        discount_percent = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
        sale_price_float = price_float * (1 - discount_percent)
        sale_price = f"{sale_price_float:.2f}"
        
        deal = {
            "product_name": product,
            "price": sale_price,
            "original_price": original_price,
            "unit": random.choice(UNITS),
            "store": store,
            "category": category,
            "image_url": None, # Could map to static placeholders if we had them
            "confidence": 1.0,
            "source": "mock_generator",
            "created_at": start_date - timedelta(days=random.randint(0, 7)) # Spread over last week
        }
        deals.append(deal)

    # 3. Batch Insert (Slow but safe loop for now, or could optimize)
    # Using existing storage.save_active_deals might handle one by one or small batch.
    # storage.save_active_deals expects a list, so we can pass it all if it handles it.
    
    # Actually storage.save_active_deals is designed for one upload batch. 
    # Let's use a direct DB insert for speed for 2000 items.
    
    values = []
    for d in deals:
        values.append((
             None, # upload_id
             d['product_name'],
             d['price'],
             d['original_price'],
             d['unit'],
             d['store'],
             d['confidence'],
             d['source'],
             d['category'],
             d['image_url'],
             d['created_at']
        ))
    
    # Chunking to avoid massive query
    chunk_size = 500
    query = """
        INSERT INTO deals (upload_id, product_name, price, original_price, unit, store, confidence, source, category, image_url, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for i in range(0, len(values), chunk_size):
        chunk = values[i:i+chunk_size]
        db.execute_many(query, chunk)
        
    print(f"Successfully inserted {len(deals)} items.")
    return len(deals)
