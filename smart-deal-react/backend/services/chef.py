"""
Service for AI-powered meal planning and recipe generation.
Uses unified AI client for retry, caching, and cost tracking.
"""
import asyncio
from typing import Dict, List, Any
from services.ai_client import get_ai_client
from services.history import PriceHistoryService

history_service = PriceHistoryService()


class ChefService:
    """AI-powered chef for meal suggestions and recipe generation."""
    
    def __init__(self):
        self.client = get_ai_client()
    
    async def suggest_menu_from_deals_async(self, deals: List[Dict]) -> Dict:
        """
        Suggest a menu based on the provided list of deals.
        Returns JSON with menu name, description, usage of deals, and savings.
        """
        if not deals:
            return self._mock_menu_suggestion()

        deal_summary = "\n".join([f"- {d.get('product', d.get('product_name', 'Item'))} (€{d.get('price', '?')})" for d in deals[:15]])
        
        prompt = f"""You are a smart budget chef. Here are the current supermarket deals:
{deal_summary}

Suggest ONE delicious dinner menu that uses as many of these deals as possible.
Return ONLY valid JSON (no markdown) with this structure:
{{
    "name": "Dish Name",
    "description": "Short appetizing description",
    "key_ingredients": ["list", "of", "ingredients", "from", "deals"],
    "total_estimated_cost": 0.00,
    "savings_note": "Why this is a good deal"
}}"""
        
        try:
            result = await self.client.generate_json(
                prompt=prompt,
                model="gemini-2.5-flash",
                feature="chef_menu"
            )
            return result
        except Exception as e:
            print(f"Error generating menu: {e}")
            return {
                "name": "Error Generating Menu",
                "description": f"Could not generate menu: {str(e)}",
                "key_ingredients": [],
                "total_estimated_cost": 0.00,
                "savings_note": "Please check API Key and logs."
            }
    
    def suggest_menu_from_deals(self, deals: List[Dict]) -> Dict:
        """Synchronous wrapper for backward compatibility."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create new task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.suggest_menu_from_deals_async(deals))
                    return future.result()
            else:
                return loop.run_until_complete(self.suggest_menu_from_deals_async(deals))
        except RuntimeError:
            return asyncio.run(self.suggest_menu_from_deals_async(deals))

    async def generate_recipe_steps_async(self, dish_name: str) -> Dict:
        """Generate detailed cooking steps for a specific dish."""
        prompt = f"""Create a simple recipe for "{dish_name}".
Return ONLY valid JSON (no markdown) with this structure:
{{
    "ingredients": ["item 1", "item 2"],
    "steps": ["Step 1", "Step 2", "Step 3"],
    "prep_time": "15 mins",
    "cooking_time": "20 mins"
}}"""
        
        try:
            return await self.client.generate_json(
                prompt=prompt,
                model="gemini-2.5-flash",
                feature="chef_recipe"
            )
        except Exception as e:
            print(f"Error generating recipe: {e}")
            return {
                "ingredients": [],
                "steps": [f"Error: {str(e)}"],
                "prep_time": "-",
                "cooking_time": "-"
            }
    
    def generate_recipe_steps(self, dish_name: str) -> Dict:
        """Synchronous wrapper for backward compatibility."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self.generate_recipe_steps_async(dish_name))
                    return future.result()
            else:
                return loop.run_until_complete(self.generate_recipe_steps_async(dish_name))
        except RuntimeError:
            return asyncio.run(self.generate_recipe_steps_async(dish_name))
    
    def plan_meal(self, dish_name: str) -> Dict:
        """Create a meal plan with ingredients matched to best deals."""
        recipe_data = self.generate_recipe_steps(dish_name)
        ingredients = recipe_data.get('ingredients', [])
        
        shopping_list_with_deals = []
        total_estimated = 0.0
        
        for item in ingredients:
            clean_item = item.split(' ')[-1] if ' ' in item else item
            best_deal = history_service.get_best_price_for_ingredient(clean_item)
            
            entry = {
                "item": item,
                "found_deal": False,
                "deal_info": None
            }
            
            if best_deal:
                entry["found_deal"] = True
                entry["deal_info"] = best_deal
                try:
                    total_estimated += float(best_deal['price'])
                except:
                    pass
            
            shopping_list_with_deals.append(entry)
            
        return {
            "dish": dish_name,
            "recipe": recipe_data,
            "shopping_list": shopping_list_with_deals,
            "total_estimated": round(total_estimated, 2)
        }
    
    def _mock_menu_suggestion(self):
        """Fallback mock data if no deals available."""
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
