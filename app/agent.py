import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv() # Load env vars from .env file

import google.auth
# Fallback to Application Default Credentials for Vertex AI if no studio key is present
if "GOOGLE_API_KEY" not in os.environ and "GOOGLE_CLOUD_PROJECT" not in os.environ:
    try:
        _, project_id = google.auth.default()
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
            os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
            os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    except Exception:
        pass

from google.adk.agents import Agent, SequentialAgent
from google.adk.apps import App
from app.tools import query_grocery

# Define structured Pydantic models for Day 4 Guardrails
class MealPlanDay(BaseModel):
    day: str = Field(description="Name of the day (e.g. Day 1, Monday)")
    meals: List[str] = Field(description="List of meals and food items for the day")
    daily_calories: float = Field(description="Aggregated calorie total for this day")
    daily_protein: float = Field(description="Aggregated protein in grams")
    daily_carbs: float = Field(description="Aggregated carbs in grams")
    daily_fat: float = Field(description="Aggregated fat in grams")

class WorkoutPlanDay(BaseModel):
    day: str = Field(description="Day name")
    exercises: List[str] = Field(description="List of exercises and durations/reps")

class WealthHealthStrategy(BaseModel):
    weekly_total_cost: float = Field(description="Total calculated grocery cost for the week matching the user's currency")
    currency: str = Field(description="USD or INR")
    within_budget_verification: bool = Field(description="True if weekly_total_cost <= user's budget, False otherwise")
    daily_nutrition_targets: List[MealPlanDay] = Field(description="Detailed daily meal plans with macros")
    exercise_routine: List[WorkoutPlanDay] = Field(description="7-day fitness routine matching target timelines and weight loss/gain goals")

# Helper function to load YAML configuration safely
def load_yaml_config(filepath: str) -> dict:
    paths = [Path(filepath), Path("../") / filepath]
    for p in paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    return {}

# Load Spec-Driven personas and manifest properties
personas_data = load_yaml_config("config/personas.yaml")
manifest_data = load_yaml_config("config/manifest.yaml")

grocery_scout_prompt = personas_data.get("personas", {}).get("GroceryScout", {}).get("system_prompt", "Search grocery data.")
habit_architect_prompt = personas_data.get("personas", {}).get("HabitArchitect", {}).get("system_prompt", "Create meal and fitness plan.")

# Initialize the models
model_name = os.environ.get("GEMINI_MODEL", manifest_data.get("model_parameters", {}).get("core_model", "gemini-1.5-pro"))

# Day 1: Single-responsibility Grocery Scout Agent
grocery_scout = Agent(
    name="grocery_scout",
    model=model_name,
    instruction=grocery_scout_prompt + "\n\nCRITICAL TOOL RULE: You must use the `query_grocery` tool to fetch food details. Pay close attention to the spelling: q-u-e-r-y-_-g-r-o-c-e-r-y (no extra 'e'). Do NOT call 'query_grocerey' or any misspelled variant.",
    tools=[query_grocery],
    description="Queries local wholesale database to fetch actual food prices and precise macronutrients."
)

# Day 1: Habit Planner Negotiation Agent
planner_negotiator = Agent(
    name="habit_planner_negotiator",
    model=model_name,
    instruction=habit_architect_prompt + "\n\nCRITICAL DELEGATION RULE: To query food ingredients, macronutrients, and pricing, you MUST transfer control to the 'grocery_scout' agent by calling the transfer_to_agent tool. You do not have direct access to the database or any tools other than delegating to grocery_scout. Do NOT attempt to call direct functions (e.g., do NOT call 'grocery_scout.get_food_items'). Always delegate.",
    sub_agents=[grocery_scout]
)

# Day 4: Strategy Formatter with Strict Output Schema Enforcement
formatter = Agent(
    name="strategy_formatter",
    model=model_name,
    instruction="Analyze the raw plan and compile the details strictly into the WealthHealthStrategy schema. Double check that the weekly_total_cost matches the sum of the grocery items and verify the within_budget_verification flag correctly.",
    output_schema=WealthHealthStrategy,
    output_key="strategy"
)

# Day 1 & Day 5: Orchestrated SequentialAgent pipeline
orchestrator = SequentialAgent(
    name="orchestrator",
    sub_agents=[planner_negotiator, formatter]
)

app = App(
    root_agent=orchestrator,
    name="app"
)
