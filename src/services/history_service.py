"""
Service for tracking product price history and identifying best deals.
Refactored to use TinyDB.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from .db import db

class PriceHistoryService:
    def __init__(self):
        self.table = db.history
        self.User = db.query

    def add_deals(self, deals: List[Dict]):
        """Add new deals to history DB."""
        timestamp = datetime.now().isoformat()
        new_entries = []
        
        for deal in deals:
            entry = {
                "product": deal.get("product", "Unknown"),
                "price": deal.get("price", 0.0),
                "store": deal.get("store", "Unknown"),
                "date": timestamp,
                "source": deal.get("source", "mock")
            }
            new_entries.append(entry)
            
        if new_entries:
            self.table.insert_multiple(new_entries)

    def get_weekly_best_buys(self) -> List[Dict]:
        """
        Identify products that are significantly cheaper this week.
        """
        all_history = self.table.all()
        if not all_history:
            return []
            
        df = pd.DataFrame(all_history)
        if df.empty:
            return []
            
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter for "current week"
        now = datetime.now()
        start_of_week = now - timedelta(days=7)
        
        current_deals = df[df['date'] >= start_of_week]
        
        if current_deals.empty:
            return []
            
        best_buys = []
        unique_products = current_deals['product'].unique()
        
        for prod in unique_products:
            # Query history for this product name
            # Ideally use fuzzy match, but for now exact containment
            product_history = df[df['product'].str.contains(prod, case=False, regex=False)]
            
            if len(product_history) < 2:
                continue 
                
            avg_price = product_history['price'].mean()
            
            current_prod_deals = current_deals[current_deals['product'] == prod]
            min_price_row = current_prod_deals.nsmallest(1, 'price').iloc[0]
            curr_price = min_price_row['price']
            
            if curr_price < (avg_price * 0.9):
                savings = (avg_price - curr_price) / avg_price
                best_buys.append({
                    "product": prod,
                    "price": curr_price,
                    "avg_price": round(avg_price, 2),
                    "store": min_price_row['store'],
                    "savings_pct": int(savings * 100),
                    "image": "🌟" 
                })
                
        best_buys.sort(key=lambda x: x['savings_pct'], reverse=True)
        return best_buys[:5]
