# app/tools.py
from skills.grocery_scout_skill import lookup_food_details

def query_grocery(food_name: str, currency: str) -> dict:
    """Searches the local wholesale grocery database for a food item and retrieves its nutritional values and price.

    Args:
        food_name: The name of the food item to search for (e.g., 'Chicken Breast', 'Eggs', 'Oatmeal').
        currency: The currency system to fetch prices for (must be 'USD' or 'INR').

    Returns:
        A dictionary containing the matched food item name, price, protein_g, carbs_g, fat_g, calories, and category.
    """
    return lookup_food_details(food_name, currency)


def query_grocerey(food_name: str, currency: str) -> dict:
    """Fallback alias for query_grocery to handle LLM spelling hallucinations.

    Args:
        food_name: The name of the food item to search for.
        currency: The currency system to fetch prices for (must be 'USD' or 'INR').

    Returns:
        A dictionary containing the matched food details.
    """
    return query_grocery(food_name, currency)
