"""
Consumer-facing view for SmartDeal Application.
This module implements the "Shopper App" mode with persistent data, real extraction integration,
and Intelligent Assistant features (Memory & AI Chef).
"""

import streamlit as st
import pandas as pd
import random
import time
import json
from datetime import datetime, timedelta
import altair as alt

# Dynamic import to handle path differences if run directly vs imported
try:
    from services import storage
    from services.history_service import PriceHistoryService
    from services.chef_service import ChefService
except ImportError:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from src.services import storage
    from src.services.history_service import PriceHistoryService
    from src.services.chef_service import ChefService

def get_mock_deals():
    """Generate realistic mock data for German supermarkets"""
    supermarkets = ["Aldi Süd", "Lidl", "Rewe", "Edeka", "Penny", "Kaufland"]
    products = [
        {"name": "Bio Bananen", "category": "Fruit", "base_price": 1.99, "image": "🍌"},
        {"name": "Irische Butter", "category": "Dairy", "base_price": 2.59, "image": "🧈"},
        {"name": "Rispentomaten", "category": "Vegetable", "base_price": 2.49, "image": "🍅"},
        {"name": "Frische Vollmilch", "category": "Dairy", "base_price": 1.19, "image": "🥛"},
        {"name": "Barilla Pasta", "category": "Pantry", "base_price": 1.89, "image": "🍝"},
        {"name": "Gemischtes Hackfleisch", "category": "Meat", "base_price": 4.99, "image": "🥩"},
        {"name": "Coca-Cola 1.5L", "category": "Drinks", "base_price": 1.79, "image": "🥤"},
        {"name": "Kombucha Bio", "category": "Drinks", "base_price": 2.99, "image": "🍹"},
        {"name": "Avocados Hass", "category": "Fruit", "base_price": 1.49, "image": "🥑"},
        {"name": "Lachsfilet", "category": "Fish", "base_price": 6.99, "image": "🐟"},
    ]
    
    deals = []
    for _ in range(10): 
        prod = random.choice(products)
        store = random.choice(supermarkets)
        discount_pct = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
        price = round(prod["base_price"] * (1 - discount_pct), 2)
        
        deals.append({
            "product": prod["name"],
            "image": prod["image"],
            "category": prod["category"],
            "store": store,
            "price": price,
            "original_price": prod["base_price"],
            "discount": f"-{int(discount_pct*100)}%",
            "expires": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%d.%m"),
            "confidence": 1.0, 
            "source": "mock"
        })
    return deals

def normalize_real_deals(real_deals):
    """Convert extracted deals to consumer format"""
    normalized = []
    for d in real_deals:
        # Handle hybrid data (nested OCR-style or flat Gemini/TinyDB-style)
        if isinstance(d.get('price'), dict):
            name = d.get('product', {}).get('text', 'Unknown Product')
            price_str = d.get('price', {}).get('value', '0')
            discount = d.get('discount', {}).get('text', 'Deal') if d.get('discount') else 'Deal'
        else:
            name = d.get('product_name', d.get('product', 'Unknown Product'))
            price_str = str(d.get('price', '0'))
            discount = d.get('discount') or 'Deal'
        
        try:
           price_val = float(price_str.replace('€', '').replace(',', '.').strip())
        except:
           price_val = 0.0

        normalized.append({
            "product": name,
            "image": "📸", 
            "category": "Extracted",
            "store": "Scanned Flyer",
            "price": price_val,
            "original_price": "N/A", 
            "discount": discount,
            "expires": "Unknown",
            "confidence": d.get('confidence', 0.5),
            "source": "real"
        })
    return normalized

def render_consumer_app():
    """Main render function for the Consumer View"""
    
    # --- INIT SERVICES ---
    if 'history_service' not in st.session_state:
        st.session_state.history_service = PriceHistoryService()
    if 'chef_service' not in st.session_state:
        st.session_state.chef_service = ChefService()

    # Load User Data
    user_list = storage.get_shopping_list()
    
    # Settings Sidebar
    with st.sidebar.expander("⚙️ Settings"):
        current_key = storage.get_api_key()
        new_key = st.text_input("Gemini API Key", value=current_key, type="password", help="Enter your Google Gemini API Key to enable the AI Chef.")
        if new_key != current_key:
            storage.save_api_key(new_key)
            st.session_state.chef_service.reload_model()
            st.toast("API Key saved!", icon="🔐")
            
    # Custom CSS
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; -webkit-font-smoothing: antialiased; }
        
        .app-header { font-size: 2.2rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #FF512F, #DD2476); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 1rem 0; margin-bottom: 0.5rem; }
        
        .deal-card-consumer { background-color: white; border-radius: 16px; padding: 1.2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid rgba(0,0,0,0.05); text-align: center; margin-bottom: 1rem; position: relative; transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .deal-card-consumer:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .real-deal-badge { position: absolute; top: 10px; right: 10px; background: #E3F2FD; color: #1565C0; font-size: 0.7rem; padding: 4px 8px; border-radius: 12px; font-weight: 700; letter-spacing: 0.5px; z-index: 2; }
        .best-buy-card { background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%); padding: 1rem; border-radius: 12px; color: #1b5e20; margin-bottom: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }

        @media (max-width: 768px) {
            .app-header { font-size: 1.8rem; }
            .deal-product-name { font-size: 0.95rem !important; }
            .deal-price-tag { font-size: 1.1rem !important; }
            .stButton button { width: 100% !important; border-radius: 12px !important; }
        }

        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;} 
        
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f8f9fa; padding: 8px; border-radius: 16px; margin-bottom: 1rem;}
        .stTabs [data-baseweb="tab"] { height: 40px; white-space: pre-wrap; border-radius: 10px; color: #666; font-weight: 600; }
        .stTabs [aria-selected="true"] { background-color: white; color: #DD2476; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="app-header">SmartShopper</div>', unsafe_allow_html=True)
    
    # --- DATA MERGE ---
    if 'mock_deals' not in st.session_state:
        st.session_state.mock_deals = get_mock_deals()
    
    all_deals = st.session_state.mock_deals.copy()
    
    # Integrate Real Data
    if 'deals' in st.session_state and st.session_state.deals:
        real_deals_norm = normalize_real_deals(st.session_state.deals)
        # Add to history if new
        current_len = len(real_deals_norm)
        last_saved = st.session_state.get('last_saved_len', 0)
        
        if current_len > last_saved:
             st.session_state.history_service.add_deals(real_deals_norm)
             st.session_state.last_saved_len = current_len
             
        all_deals = real_deals_norm + all_deals
        
    # Check for Watchlist Matches
    matches = []
    for item in user_list:
        for deal in all_deals:
            if item.lower() in deal['product'].lower():
                matches.append(f"{deal['product']} (€{deal['price']})")
    
    # Tabs
    tab_title_feed = "🔥 Feed"
    tab_title_list = f"📝 List ({len(matches)})" if matches else "📝 List"
    
    tab_feed, tab_list, tab_brain, tab_chef = st.tabs([tab_title_feed, tab_title_list, "🧠 Brain", "👨‍🍳 AI Chef"])
    
    # --- TAB 1: FEED ---
    with tab_feed:
        if matches:
             st.success(f"Found {len(matches)} items from your list!")
             
        cols = st.columns(3)
        for i, deal in enumerate(all_deals):
            with cols[i % 3]:
                is_real = deal.get('source') == 'real'
                badge_html = '<div class="real-deal-badge">SCANNED</div>' if is_real else ''
                img_display = deal['image']
                price_color = "#DD2476" if not is_real else "#2196F3"
                
                # Use dedent or concise string to avoid markdown code block interpretation
                html_card = f"""<div class="deal-card-consumer" style="min-height: 260px; display: flex; flex-direction: column; justify-content: space-between;">
                    {badge_html}
                    <div>
                        <div style="font-size:3.5rem; margin-bottom: 0.5rem; line-height: 1;">{img_display}</div>
                        <div class="deal-product-name" style="font-weight:700; font-size:1.05rem; height:2.4em; overflow:hidden; line-height: 1.2; color: #333;">{deal['product']}</div>
                        <div style="color:#999; font-size:0.75rem; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.5px;">{deal['store']}</div>
                    </div>
                    <div>
                         <div class="deal-price-tag" style="color:{price_color}; font-weight:800; font-size:1.3rem;">€{deal['price']}</div>
                         {f'<div style="font-size: 0.75rem; color: #4CAF50; font-weight: 600;">{deal["discount"]}</div>' if deal.get('discount') else '<div style="height:14px"></div>'}
                    </div>
                </div>"""
                
                st.markdown(html_card, unsafe_allow_html=True)
                
                if st.button("Add to Cart", key=f"btn_{i}_{deal.get('product')}", use_container_width=True):
                    storage.add_to_list(deal['product'])
                    st.toast(f"Added {deal['product']}!", icon="🛒")
                    time.sleep(0.5) 
                    st.rerun()

    # --- TAB 2: LIST ---
    with tab_list:
        st.markdown("### 📝 Smart Shopping List")
        c1, c2 = st.columns([3, 1])
        new_item = c1.text_input("Add Item", placeholder="e.g. Milk", label_visibility="collapsed")
        if c2.button("Add", use_container_width=True):
            if new_item:
                storage.add_to_list(new_item)
                st.rerun()

        current_list = storage.get_shopping_list()
        if not current_list:
             st.markdown("""<div style="text-align: center; padding: 2rem; color: #888;"><div style="font-size: 3rem; margin-bottom: 1rem;">🛒</div>Your list is empty.</div>""", unsafe_allow_html=True)
        
        for item in current_list:
            match = next((d for d in all_deals if item.lower() in d['product'].lower()), None)
            with st.container():
                st.markdown(f"""<div style="background: white; padding: 12px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 8px;"><div style="font-weight: 600; font-size: 1.1rem; color: #333;">{item}</div></div>""", unsafe_allow_html=True)
                col_status, col_act = st.columns([4, 1])
                with col_status:
                    if match:
                        st.success(f"Deal: {match['product']} (€{match['price']})")
                    else:
                        st.caption("Searching for deals...")
                with col_act:
                    if st.button("🗑️", key=f"del_{item}"):
                        storage.remove_from_list(item)
                        st.rerun()

    # --- TAB 3: BRAIN (HISTORY) ---
    with tab_brain:
        st.markdown("### 🧠 Smart Assistant")
        st.write("I remember prices so you don't have to.")
        
        # 1. Weekly Best Buys
        st.markdown("#### 🏆 Weekly Best Buys")
        best_buys = st.session_state.history_service.get_weekly_best_buys()
        
        if best_buys:
            for deal in best_buys:
                st.markdown(f"""
                <div class="best-buy-card">
                    <div style="font-weight:bold; font-size:1.1rem;">{deal['product']}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:1.3rem;">€{deal['price']}</span>
                            <span style="text-decoration:line-through; font-size:0.9rem; opacity:0.7;">€{deal['avg_price']}</span>
                        </div>
                        <div style="background:white; padding:4px 8px; border-radius:8px; font-weight:bold;">
                            Save {deal['savings_pct']}%
                        </div>
                    </div>
                    <div style="font-size:0.8rem; margin-top:4px;">at {deal['store']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("I'm learning! Scan more flyers to see 'Best Buy' recommendations based on history.")
            
        # 2. Historical Trend Chart
        st.markdown("#### 📉 Price Watch")
        # Reuse previous chart logic but now it could be dynamic
        dates = pd.date_range(end=datetime.now(), periods=30)
        prices = [2.59 + random.uniform(-0.4, 0.4) for _ in range(30)]
        df_trend = pd.DataFrame({"Date": dates, "Price": prices})
        chart = alt.Chart(df_trend).mark_line(point=True).encode(x='Date', y=alt.Y('Price', scale=alt.Scale(domain=[1, 3])), tooltip=['Date', 'Price']).properties(height=200)
        st.altair_chart(chart, use_container_width=True)

    # --- TAB 4: AI CHEF ---
    with tab_chef:
        st.markdown("### 👨‍🍳 AI Chef")
        st.write("Turn today's deals into tonight's dinner.")
        
        # Input Mode
        if "chef_result" not in st.session_state:
            st.session_state.chef_result = None

        col_in, col_btn = st.columns([3, 1])
        dish_request = col_in.text_input("What are you craving?", placeholder="e.g. Pasta, Low carb, Fast dinner")
        
        if col_btn.button("Inspire Me", use_container_width=True):
            if dish_request:
                # Generate specific recipe
                # For demo, using suggest_menu logic or recipe logic?
                # Let's try suggest_menu first if input is vague, or recipe if specific.
                # Simplification: Always use suggest_menu based on deals to show off integration
                with st.spinner("Chef is checking prices..."):
                    result = st.session_state.chef_service.suggest_menu_from_deals(all_deals)
                    st.session_state.chef_result = result
            else:
                 # Suggest based on deals
                 with st.spinner("Thinking..."):
                    result = st.session_state.chef_service.suggest_menu_from_deals(all_deals)
                    st.session_state.chef_result = result
                    
        # Display Result
        if st.session_state.chef_result:
            res = st.session_state.chef_result
            
            st.markdown("---")
            st.markdown(f"## 🍽️ {res.get('name', 'Special Dish')}")
            st.write(res.get('description', ''))
            
            st.markdown(f"**💰 Estimated Cost:** €{res.get('total_estimated_cost', 0.00):.2f}")
            st.success(res.get('savings_note', 'Great value!'))
            
            st.markdown("### 🛒 Ingredients")
            ingredients = res.get('key_ingredients', [])
            for ing in ingredients:
                st.markdown(f"- {ing}")
                
            if st.button("Add All to Shopping List", key="add_recipe"):
                for ing in ingredients:
                    storage.add_to_list(ing)
                st.toast("Ingredients added to list!", icon="✅")
                time.sleep(1)
                st.rerun()

if __name__ == "__main__":
    render_consumer_app()
