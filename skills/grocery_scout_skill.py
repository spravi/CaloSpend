# grocery_scout_skill.py
import json
from pathlib import Path

def load_grocery_db() -> dict:
    """Loads the local JSON grocery lookup database.
    
    Returns:
        A dictionary containing the list of available foods and nutritional details.
    """
    # Look for database in standard relative paths
    paths_to_try = [
        Path(__file__).parent / "grocery_lookup.json",
        Path("skills/grocery_lookup.json"),
        Path("../skills/grocery_lookup.json")
    ]
    for p in paths_to_try:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    # Default fallback database if files are missing
    return {
        "foods": [
            {"name": "Oatmeal", "price_usd": 0.40, "price_inr": 30.0, "protein_g": 13.0, "carbs_g": 68.0, "fat_g": 6.5, "calories": 379.0, "category": "Carbs"},
            {"name": "Chicken Breast", "price_usd": 1.50, "price_inr": 120.0, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6, "calories": 165.0, "category": "Protein"},
            {"name": "Eggs", "price_usd": 0.60, "price_inr": 45.0, "protein_g": 12.6, "carbs_g": 0.7, "fat_g": 9.5, "calories": 143.0, "category": "Protein"},
            {"name": "Tofu", "price_usd": 0.80, "price_inr": 60.0, "protein_g": 8.0, "carbs_g": 1.9, "fat_g": 4.8, "calories": 76.0, "category": "Protein"}
        ]
    }

def lookup_food_details(food_name: str, currency: str) -> dict:
    """Searches the grocery database for a food item and retrieves its nutritional values and price.

    Args:
        food_name: The name of the food item to search for (e.g., 'Chicken Breast', 'Eggs', 'Oatmeal').
        currency: The currency system to fetch prices for (must be 'USD' or 'INR').

    Returns:
        A dictionary containing the matched food item name, price, protein_g, carbs_g, fat_g, calories, and category.
    """
    db = load_grocery_db()
    query_lower = food_name.lower()
    
    # Try exact or partial matches
    for food in db.get("foods", []):
        if food["name"].lower() in query_lower or query_lower in food["name"].lower():
            price = food["price_inr"] if currency.upper() == "INR" else food["price_usd"]
            return {
                "name": food["name"],
                "price": float(price),
                "protein_g": float(food["protein_g"]),
                "carbs_g": float(food["carbs_g"]),
                "fat_g": float(food["fat_g"]),
                "calories": float(food["calories"]),
                "category": food["category"],
                "currency": currency.upper()
            }
            
    # Return descriptive error if not found to prevent system crash
    return {"error": f"Item '{food_name}' was not found in the local lookup database."}
