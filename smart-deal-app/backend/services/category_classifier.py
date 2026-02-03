"""
Category Classifier Service
Classifies products into categories using keyword matching + Gemini fallback.
"""

import os
import re
from typing import Optional

# Category definitions with German keywords
CATEGORY_KEYWORDS = {
    "Dairy": [
        "milch", "käse", "joghurt", "butter", "sahne", "quark", "frischkäse",
        "mozzarella", "gouda", "emmentaler", "camembert", "feta", "skyr",
        "schmand", "kefir", "lactose", "molke", "pudding", "dessert",
        "cream", "milk", "cheese", "yogurt", "yoghurt"
    ],
    "Meat": [
        "fleisch", "hack", "steak", "filet", "schnitzel", "wurst", "schinken",
        "salami", "speck", "bacon", "hähnchen", "huhn", "hühner", "pute",
        "rind", "schwein", "lamm", "kalb", "braten", "gulasch", "rouladen",
        "bratwurst", "wiener", "leberwurst", "mettwurst", "aufschnitt",
        "chicken", "beef", "pork", "meat", "sausage", "ham"
    ],
    "Seafood": [
        "fisch", "lachs", "thunfisch", "forelle", "kabeljau", "hering",
        "garnelen", "shrimp", "meeresfrüchte", "krabben", "muscheln",
        "fish", "salmon", "tuna", "seafood", "shrimp"
    ],
    "Produce": [
        "obst", "gemüse", "apfel", "birne", "banane", "orange", "zitrone",
        "erdbeere", "himbeere", "traube", "kiwi", "mango", "ananas",
        "tomate", "gurke", "paprika", "zwiebel", "kartoffel", "karotte",
        "salat", "spinat", "brokkoli", "blumenkohl", "zucchini", "avocado",
        "pilze", "champignon", "lauch", "sellerie", "radieschen",
        "fruit", "vegetable", "apple", "banana", "tomato", "potato"
    ],
    "Beverages": [
        "getränk", "wasser", "saft", "cola", "fanta", "sprite", "limonade",
        "bier", "wein", "sekt", "champagner", "wodka", "whisky", "rum",
        "kaffee", "tee", "kakao", "energy", "red bull", "monster",
        "drink", "juice", "beer", "wine", "coffee", "tea", "water"
    ],
    "Bakery": [
        "brot", "brötchen", "semmel", "croissant", "baguette", "toast",
        "kuchen", "torte", "muffin", "donut", "brezel", "laugen",
        "bread", "roll", "cake", "pastry", "bakery"
    ],
    "Snacks": [
        "chips", "snack", "nüsse", "erdnüsse", "cashew", "mandeln",
        "schokolade", "schoko", "bonbon", "gummibärchen", "haribo",
        "keks", "cookies", "riegel", "müsli", "cornflakes",
        "chocolate", "candy", "nuts", "cookies", "crackers"
    ],
    "Frozen": [
        "tiefkühl", "gefroren", "eis", "eiscreme", "pizza", "pommes",
        "fischstäbchen", "spinat", "gemüse tiefgekühlt",
        "frozen", "ice cream", "pizza"
    ],
    "Pantry": [
        "nudel", "pasta", "spaghetti", "reis", "mehl", "zucker", "salz",
        "öl", "essig", "soße", "sauce", "ketchup", "senf", "mayo",
        "konserve", "dose", "marmelade", "honig", "nutella", "aufstrich",
        "gewürz", "pfeffer", "paprika pulver",
        "noodle", "rice", "flour", "sugar", "oil", "sauce"
    ],
    "Hygiene": [
        "shampoo", "duschgel", "seife", "zahnpasta", "deo", "deodorant",
        "toilettenpapier", "küchenrolle", "taschentuch", "waschmittel",
        "spülmittel", "reiniger", "hygiene", "pflege", "creme", "lotion",
        "rasierer", "after shave", "parfüm",
        "soap", "toothpaste", "detergent", "cleaner", "shampoo"
    ],
    "Pet": [
        "katze", "hund", "tier", "futter", "katzenfutter", "hundefutter",
        "streu", "katzenstreu", "leckerli",
        "cat", "dog", "pet", "food pet"
    ],
    "Baby": [
        "baby", "windel", "pampers", "brei", "milchpulver", "säugling",
        "diaper", "baby food"
    ]
}


def classify_by_keywords(product_name: str) -> Optional[str]:
    """
    Classify a product using keyword matching.
    
    Args:
        product_name: The product name to classify
    
    Returns:
        Category name or None if no match
    """
    name_lower = product_name.lower()
    
    # Check each category
    best_match = None
    best_score = 0
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in name_lower:
                # Longer keywords get higher scores
                score += len(keyword)
        
        if score > best_score:
            best_score = score
            best_match = category
    
    return best_match if best_score > 0 else None


def classify_with_gemini(product_name: str) -> Optional[str]:
    """
    Classify a product using Gemini Flash Lite for ambiguous cases.
    
    Args:
        product_name: The product name to classify
    
    Returns:
        Category name or None if failed
    """
    try:
        import google.generativeai as genai
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        
        categories = list(CATEGORY_KEYWORDS.keys())
        prompt = f"""Classify this German supermarket product into exactly ONE category.

Product: {product_name}

Categories: {', '.join(categories)}

Respond with ONLY the category name, nothing else."""

        response = model.generate_content(prompt)
        result = response.text.strip()
        
        # Validate the response
        if result in categories:
            return result
        
        # Try to find a close match
        result_lower = result.lower()
        for cat in categories:
            if cat.lower() in result_lower:
                return cat
        
        return "Other"
        
    except Exception as e:
        print(f"  ⚠️ Gemini classification failed: {e}")
        return None


def classify_product(product_name: str, use_ai_fallback: bool = True) -> str:
    """
    Classify a product into a category.
    
    First tries keyword matching, then falls back to Gemini if enabled.
    
    Args:
        product_name: The product name to classify
        use_ai_fallback: Whether to use Gemini for ambiguous cases
    
    Returns:
        Category name (defaults to "Other" if all else fails)
    """
    # Try keyword matching first
    category = classify_by_keywords(product_name)
    
    if category:
        return category
    
    # Try AI classification if enabled
    if use_ai_fallback:
        category = classify_with_gemini(product_name)
        if category:
            return category
    
    return "Other"


def batch_classify(product_names: list, use_ai_fallback: bool = True) -> dict:
    """
    Classify multiple products.
    
    Args:
        product_names: List of product names
        use_ai_fallback: Whether to use Gemini for ambiguous cases
    
    Returns:
        Dict mapping product_name to category
    """
    results = {}
    ai_needed = []
    
    # First pass: keyword matching
    for name in product_names:
        category = classify_by_keywords(name)
        if category:
            results[name] = category
        else:
            ai_needed.append(name)
    
    # Second pass: AI for unknowns (if enabled)
    if use_ai_fallback and ai_needed:
        print(f"  🤖 Using AI to classify {len(ai_needed)} products...")
        for name in ai_needed:
            results[name] = classify_with_gemini(name) or "Other"
    else:
        for name in ai_needed:
            results[name] = "Other"
    
    return results


if __name__ == "__main__":
    # Test classification
    test_products = [
        "Monster Energy Drink",
        "Schweine-Filet",
        "REWE Beste Wahl Bananen",
        "Nutella",
        "Gourmet Gold Katzennahrung",
        "Ehrmann High Protein Pudding",
        "Beck's Bier",
    ]
    
    print("Testing category classification:\n")
    for product in test_products:
        category = classify_product(product, use_ai_fallback=False)
        print(f"  {product} → {category}")
