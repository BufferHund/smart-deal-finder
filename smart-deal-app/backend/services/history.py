from db import db
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta

class PriceHistoryService:
    def get_weekly_best_buys(self) -> List[Dict]:
        """
        Get the best deals for each product from the last 7 days.
        Returns a list of dicts with product, best_price, store, etc.
        """
        # SQL query to find lowest price per product in last 7 days
        query = """
        SELECT product_name, MIN(price) as best_price, store, unit, source, created_at
        FROM deals
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY product_name
        ORDER BY best_price ASC
        """
        results = db.execute_query(query)
        
        best_buys = []
        for r in results:
            best_buys.append({
                "product": r['product_name'], # Frontend expects 'product'
                "price": float(r['best_price']),
                "store": r['store'],
                "unit": r['unit'],
                "date": str(r['created_at'])
            })
            
        return best_buys

    def get_best_price_for_ingredient(self, ingredient_name: str) -> Optional[Dict]:
        """
        Find the best historical price for a specific ingredient (fuzzy match).
        """
        # Simple SQL LIKE search
        query = """
        SELECT product_name, price, store, unit, created_at
        FROM deals
        WHERE product_name LIKE %s
        ORDER BY price ASC
        LIMIT 1
        """
        params = (f"%{ingredient_name}%",)
        results = db.execute_query(query, params)
        
        if results:
            r = results[0]
            return {
                "product": r['product_name'],
                "price": float(r['price']),
                "store": r['store'],
                "unit": r['unit'],
                "found_at": str(r['created_at'])
            }
        return None
