"""
SmartDeal User App - Mobile-First Shopping Assistant

A consumer-facing application that provides:
- Personalized product recommendations based on location and preferences
- Price history and trends
- Recipe suggestions based on available deals
- Supermarket comparison
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Page configuration - Mobile optimized
st.set_page_config(
    page_title="SmartDeal - Dein Einkaufsassistent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-first CSS styling
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.5rem;
        }
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Card styling */
    .deal-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }

    .price-tag {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
    }

    .discount-badge {
        background: #ff4757;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
    }

    .supermarket-badge {
        background: #f1f2f6;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin-right: 0.5rem;
    }

    /* Recipe card */
    .recipe-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    /* Bottom navigation */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        padding: 0.75rem;
        display: flex;
        justify-content: space-around;
        z-index: 1000;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'favorite_supermarkets' not in st.session_state:
    st.session_state.favorite_supermarkets = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Sample data generation (replace with real data later)
def generate_sample_deals(location=None, supermarkets=None):
    """Generate sample deals based on user preferences"""
    products = [
        {"name": "Bio-Äpfel", "category": "Obst & Gemüse", "base_price": 2.99},
        {"name": "Vollmilch 3.5%", "category": "Milchprodukte", "base_price": 1.29},
        {"name": "Hähnchenbrust", "category": "Fleisch", "base_price": 7.99},
        {"name": "Spaghetti", "category": "Nudeln & Reis", "base_price": 1.49},
        {"name": "Tomatensoße", "category": "Konserven", "base_price": 1.99},
        {"name": "Coca Cola 1.5L", "category": "Getränke", "base_price": 1.79},
        {"name": "Nutella 450g", "category": "Brotaufstrich", "base_price": 3.99},
        {"name": "Butter 250g", "category": "Milchprodukte", "base_price": 2.49},
        {"name": "Kaffee gemahlen", "category": "Kaffee & Tee", "base_price": 5.99},
        {"name": "Brot Vollkorn", "category": "Backwaren", "base_price": 2.79},
    ]

    supermarket_list = supermarkets if supermarkets else ["REWE", "Edeka", "Aldi", "Lidl", "Penny"]

    deals = []
    for product in products:
        for _ in range(random.randint(1, 3)):
            discount = random.randint(10, 50)
            original_price = product["base_price"]
            current_price = round(original_price * (1 - discount/100), 2)

            deals.append({
                "product_name": product["name"],
                "category": product["category"],
                "current_price": current_price,
                "original_price": original_price,
                "discount_percent": discount,
                "supermarket": random.choice(supermarket_list),
                "unit": "1kg" if product["category"] in ["Obst & Gemüse", "Fleisch"] else "Stück",
                "valid_until": (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%d.%m.%Y")
            })

    return pd.DataFrame(deals)

def generate_price_history(product_name):
    """Generate sample price history for a product"""
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    base_price = random.uniform(2, 10)
    prices = [base_price + random.uniform(-1, 1) for _ in range(30)]

    return pd.DataFrame({
        'date': dates,
        'price': prices,
        'supermarket': random.choices(['REWE', 'Edeka', 'Aldi', 'Lidl'], k=30)
    })

def generate_recipe_suggestions(available_deals):
    """Generate recipe suggestions based on available deals"""
    recipes = [
        {
            "name": "Spaghetti Bolognese",
            "ingredients": ["Spaghetti", "Hackfleisch", "Tomatensoße", "Zwiebeln"],
            "difficulty": "Einfach",
            "time": "30 Min",
            "servings": 4,
            "estimated_cost": 8.50
        },
        {
            "name": "Hähnchen mit Gemüse",
            "ingredients": ["Hähnchenbrust", "Paprika", "Zucchini", "Karotten"],
            "difficulty": "Mittel",
            "time": "45 Min",
            "servings": 2,
            "estimated_cost": 12.00
        },
        {
            "name": "Apfelkuchen",
            "ingredients": ["Äpfel", "Mehl", "Butter", "Zucker", "Eier"],
            "difficulty": "Mittel",
            "time": "60 Min",
            "servings": 8,
            "estimated_cost": 6.50
        }
    ]
    return recipes

# Main app
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🛒 SmartDeal</h1>
        <p>Dein intelligenter Einkaufsassistent</p>
    </div>
    """, unsafe_allow_html=True)

    # Check if user has completed onboarding
    if st.session_state.user_location is None:
        show_onboarding()
    else:
        show_main_app()

def show_onboarding():
    """Onboarding flow for new users"""
    st.markdown("### 👋 Willkommen bei SmartDeal!")
    st.markdown("Beantworte zwei kurze Fragen für personalisierte Angebote:")

    with st.form("onboarding_form"):
        # Location selection
        st.markdown("#### 📍 Wo bist du?")
        location = st.text_input(
            "Stadt oder PLZ",
            placeholder="z.B. Berlin, 10115",
            help="Wir zeigen dir Angebote in deiner Nähe"
        )

        # Supermarket preferences
        st.markdown("#### 🏪 Welche Supermärkte besuchst du?")
        col1, col2 = st.columns(2)
        with col1:
            rewe = st.checkbox("REWE", value=True)
            aldi = st.checkbox("Aldi")
            penny = st.checkbox("Penny")
        with col2:
            edeka = st.checkbox("Edeka", value=True)
            lidl = st.checkbox("Lidl")
            kaufland = st.checkbox("Kaufland")

        submitted = st.form_submit_button("Los geht's! 🚀", use_container_width=True)

        if submitted:
            if not location:
                st.error("Bitte gib deinen Standort an")
            else:
                selected_markets = []
                if rewe: selected_markets.append("REWE")
                if edeka: selected_markets.append("Edeka")
                if aldi: selected_markets.append("Aldi")
                if lidl: selected_markets.append("Lidl")
                if penny: selected_markets.append("Penny")
                if kaufland: selected_markets.append("Kaufland")

                if not selected_markets:
                    st.error("Bitte wähle mindestens einen Supermarkt aus")
                else:
                    st.session_state.user_location = location
                    st.session_state.favorite_supermarkets = selected_markets
                    st.rerun()

def show_main_app():
    """Main application interface"""
    # Navigation tabs (mobile-friendly)
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Angebote", "📊 Preistrends", "🍳 Rezepte", "⚙️ Einstellungen"])

    with tab1:
        show_deals_tab()

    with tab2:
        show_price_trends_tab()

    with tab3:
        show_recipes_tab()

    with tab4:
        show_settings_tab()

def show_deals_tab():
    """Display personalized deals"""
    st.markdown(f"### 🎯 Angebote für dich")
    st.markdown(f"📍 {st.session_state.user_location}")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox(
            "Kategorie",
            ["Alle", "Obst & Gemüse", "Milchprodukte", "Fleisch", "Getränke", "Backwaren"]
        )
    with col2:
        sort_by = st.selectbox(
            "Sortieren",
            ["Höchster Rabatt", "Niedrigster Preis", "Ablaufdatum"]
        )

    # Generate and filter deals
    deals_df = generate_sample_deals(
        location=st.session_state.user_location,
        supermarkets=st.session_state.favorite_supermarkets
    )

    if category_filter != "Alle":
        deals_df = deals_df[deals_df['category'] == category_filter]

    # Sort deals
    if sort_by == "Höchster Rabatt":
        deals_df = deals_df.sort_values('discount_percent', ascending=False)
    elif sort_by == "Niedrigster Preis":
        deals_df = deals_df.sort_values('current_price', ascending=True)

    # Display deals as cards
    for idx, deal in deals_df.head(10).iterrows():
        savings = deal['original_price'] - deal['current_price']

        st.markdown(f"""
        <div class="deal-card">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 0.5rem 0;">{deal['product_name']}</h3>
                    <span class="supermarket-badge">{deal['supermarket']}</span>
                    <span class="discount-badge">-{deal['discount_percent']}%</span>
                    <p style="color: #666; margin: 0.5rem 0;">
                        Gültig bis {deal['valid_until']}
                    </p>
                </div>
                <div style="text-align: right;">
                    <div class="price-tag">€{deal['current_price']:.2f}</div>
                    <div style="text-decoration: line-through; color: #999;">
                        €{deal['original_price']:.2f}
                    </div>
                    <div style="color: #27ae60; font-weight: bold; font-size: 0.9rem;">
                        Spare €{savings:.2f}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(f"Zur Merkliste", key=f"watch_{idx}", use_container_width=True):
                if deal['product_name'] not in st.session_state.watchlist:
                    st.session_state.watchlist.append(deal['product_name'])
                    st.success(f"✓ {deal['product_name']} zur Merkliste hinzugefügt")
        with col2:
            if st.button("📊", key=f"trend_{idx}"):
                st.session_state['selected_product'] = deal['product_name']
                st.info(f"Wechsle zu Preistrends für {deal['product_name']}")

def show_price_trends_tab():
    """Display price trends and history"""
    st.markdown("### 📊 Preisentwicklung")

    # Product selection
    product_name = st.selectbox(
        "Produkt auswählen",
        ["Vollmilch 3.5%", "Bio-Äpfel", "Hähnchenbrust", "Nutella 450g", "Kaffee gemahlen"],
        index=0 if 'selected_product' not in st.session_state else 0
    )

    # Time range selection
    time_range = st.radio(
        "Zeitraum",
        ["7 Tage", "30 Tage", "90 Tage"],
        horizontal=True
    )

    # Generate price history
    price_history = generate_price_history(product_name)

    # Price trend chart
    fig = go.Figure()

    for market in price_history['supermarket'].unique():
        market_data = price_history[price_history['supermarket'] == market]
        fig.add_trace(go.Scatter(
            x=market_data['date'],
            y=market_data['price'],
            mode='lines+markers',
            name=market,
            line=dict(width=2)
        ))

    fig.update_layout(
        title=f"Preisentwicklung: {product_name}",
        xaxis_title="Datum",
        yaxis_title="Preis (€)",
        hovermode='x unified',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Price statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Aktueller Preis",
            f"€{price_history['price'].iloc[-1]:.2f}"
        )
    with col2:
        avg_price = price_history['price'].mean()
        st.metric(
            "Durchschnitt",
            f"€{avg_price:.2f}"
        )
    with col3:
        min_price = price_history['price'].min()
        st.metric(
            "Bester Preis",
            f"€{min_price:.2f}",
            delta=f"-{((avg_price - min_price) / avg_price * 100):.1f}%"
        )

    # Price alerts
    st.markdown("#### 🔔 Preisalarm einrichten")
    target_price = st.number_input(
        f"Benachrichtige mich wenn der Preis unter € liegt",
        min_value=0.0,
        max_value=20.0,
        value=float(min_price),
        step=0.10
    )

    if st.button("Alarm aktivieren", use_container_width=True):
        st.success(f"✓ Preisalarm für {product_name} bei €{target_price:.2f} aktiviert!")

def show_recipes_tab():
    """Display recipe suggestions based on deals"""
    st.markdown("### 🍳 Rezeptvorschläge")
    st.markdown("Basierend auf aktuellen Angeboten")

    deals_df = generate_sample_deals(
        location=st.session_state.user_location,
        supermarkets=st.session_state.favorite_supermarkets
    )

    recipes = generate_recipe_suggestions(deals_df)

    for recipe in recipes:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>{recipe['name']}</h3>
            <div style="display: flex; gap: 1rem; margin: 0.5rem 0; flex-wrap: wrap;">
                <span>⏱️ {recipe['time']}</span>
                <span>👥 {recipe['servings']} Portionen</span>
                <span>💰 ~€{recipe['estimated_cost']:.2f}</span>
                <span>📊 {recipe['difficulty']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("Zutaten und Angebote"):
            st.markdown("**Benötigte Zutaten:**")
            for ingredient in recipe['ingredients']:
                # Check if ingredient is on sale
                matching_deals = deals_df[
                    deals_df['product_name'].str.contains(ingredient, case=False, na=False)
                ]

                if len(matching_deals) > 0:
                    best_deal = matching_deals.iloc[0]
                    st.markdown(f"✓ {ingredient} - **Im Angebot bei {best_deal['supermarket']}** (€{best_deal['current_price']:.2f}, -{best_deal['discount_percent']}%)")
                else:
                    st.markdown(f"• {ingredient}")

            if st.button(f"Rezept kochen", key=f"cook_{recipe['name']}", use_container_width=True):
                st.success(f"🎉 Viel Spaß beim Kochen von {recipe['name']}!")

def show_settings_tab():
    """User settings and preferences"""
    st.markdown("### ⚙️ Einstellungen")

    # Location
    st.markdown("#### 📍 Standort")
    new_location = st.text_input(
        "Stadt oder PLZ",
        value=st.session_state.user_location
    )

    if new_location != st.session_state.user_location:
        if st.button("Standort aktualisieren"):
            st.session_state.user_location = new_location
            st.success("✓ Standort aktualisiert")
            st.rerun()

    # Supermarkets
    st.markdown("#### 🏪 Bevorzugte Supermärkte")
    supermarkets = ["REWE", "Edeka", "Aldi", "Lidl", "Penny", "Kaufland", "Netto"]
    selected = st.multiselect(
        "Wähle deine Supermärkte",
        supermarkets,
        default=st.session_state.favorite_supermarkets
    )

    if selected != st.session_state.favorite_supermarkets:
        if st.button("Supermärkte aktualisieren"):
            st.session_state.favorite_supermarkets = selected
            st.success("✓ Supermärkte aktualisiert")
            st.rerun()

    # Watchlist
    st.markdown("#### ⭐ Meine Merkliste")
    if st.session_state.watchlist:
        for item in st.session_state.watchlist:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"• {item}")
            with col2:
                if st.button("❌", key=f"remove_{item}"):
                    st.session_state.watchlist.remove(item)
                    st.rerun()
    else:
        st.info("Deine Merkliste ist leer. Füge Produkte aus den Angeboten hinzu!")

    # Notifications
    st.markdown("#### 🔔 Benachrichtigungen")
    st.checkbox("Preisalarme aktivieren", value=True)
    st.checkbox("Wöchentliche Angebots-Zusammenfassung", value=True)
    st.checkbox("Neue Rezeptvorschläge", value=False)

    # About
    st.markdown("---")
    st.markdown("#### ℹ️ Über SmartDeal")
    st.markdown("""
    SmartDeal hilft dir, Geld beim Einkaufen zu sparen durch:
    - Personalisierte Angebote in deiner Nähe
    - Preisentwicklung und Trends
    - Rezeptvorschläge basierend auf Angeboten
    - Preisalarme für deine Lieblingsprodukte

    Version 1.0.0 | Made with ❤️
    """)

if __name__ == "__main__":
    main()
