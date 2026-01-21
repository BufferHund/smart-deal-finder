"""
Service for AI-powered meal planning and recipe generation.
Uses Google Gemini to create recipes based on available deals.
"""
import os
import json
import google.generativeai as genai
from typing import Dict, List, Any

# Configure API
def get_configured_key():
    """Get API key from environment or storage."""
    env_key = os.getenv("GOOGLE_API_KEY")
    if env_key:
        return env_key
    
    # Try dynamic import to avoid circular dependency issues if running standalone
    try:
        from services import storage
        return storage.get_api_key()
    except ImportError:
        # Fallback for relative import
        try:
            import sys
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
            from src.services import storage
            return storage.get_api_key()
        except:
            return None

class ChefService:
    def __init__(self):
        self.reload_model()

    def reload_model(self):
        """Reload model with current API key."""
        api_key = get_configured_key()
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None

    def suggest_menu_from_deals(self, deals: List[Dict]) -> Dict:
        """
        Suggest a menu based on the provided list of deals.
        Returns JSON with menu name, description, usage of deals, and savings.
        """
        if not self.model:
            return self._mock_menu_suggestion()

        # Prepare context for LLM
        deal_summary = "\n".join([f"- {d['product']} (€{d['price']})" for d in deals[:15]])
        
        prompt = f"""
        You are a smart budget chef. Here are the current supermarket deals:
        {deal_summary}
        
        Suggest ONE delicious dinner menu that uses as many of these deals as possible.
        Return ONLY valid JSON (no markdown) with this structure:
        {{
            "name": "Dish Name",
            "description": "Short appetizing description",
            "key_ingredients": ["list", "of", "ingredients", "from", "deals"],
            "total_estimated_cost": 0.00,
            "savings_note": "Why this is a good deal"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            print(f"DEBUG: Gemini Menu Response: {response.text}") # Debug log
            
            # Simple cleanup if the model returns markdown code blocks
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error generating menu: {e}")
            return self._mock_menu_suggestion()

    def generate_recipe_steps(self, dish_name: str) -> Dict:
        """
        Generate detailed cooking steps for a specific dish.
        """
        if not self.model:
            return self._mock_recipe_steps(dish_name)
            
        prompt = f"""
        Create a simple recipe for "{dish_name}".
        Return ONLY valid JSON (no markdown) with this structure:
        {{
            "ingredients": ["item 1", "item 2"],
            "steps": ["Step 1", "Step 2", "Step 3"],
            "prep_time": "15 mins",
            "cooking_time": "20 mins"
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error generating recipe: {e}")
            return self._mock_recipe_steps(dish_name)

    def _mock_menu_suggestion(self):
        """Fallback mock data if API fails"""
        return {
            "name": "Mock Mediterranean Pasta",
            "description": "A classic pasta dish using on-sale tomatoes and fresh herbs.",
            "key_ingredients": ["Barilla Pasta", "Rispentomaten", "Irische Butter"],
            "total_estimated_cost": 4.50,
            "savings_note": "Uses 3 ingredients currently on top discount!"
        }

    def _mock_recipe_steps(self, dish_name):
        return {
            "ingredients": ["Pasta", "Tomatoes", "Garlic", "Olive Oil"],
            "steps": [
                "Boil water and cook pasta al dente.",
                "Chop tomatoes and sauté with garlic.",
                "Toss pasta in the sauce.",
                "Serve hot with cheese."
            ],
            "prep_time": "10 mins",
            "cooking_time": "15 mins"
        }
