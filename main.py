# main.py
import argparse
import asyncio
import json

from dotenv import load_dotenv

load_dotenv()  # Load env vars from .env file

# Import sanitization and safety utilities
# Import ADK elements
from google.adk.runners import InMemoryRunner

from app.security import sanitize_budget, sanitize_input_text


async def run_cli_strategy(
    budget: float, currency: str, calorie_target: float, goal: str, preferences: str
):
    """Executes the agent strategy generation offline via the console."""

    # 1. Sanitize
    clean_goal = sanitize_input_text(goal)
    clean_preferences = sanitize_input_text(preferences)
    clean_budget = sanitize_budget(budget)
    clean_currency = "INR" if currency.upper() == "INR" else "USD"

    user_prompt = (
        f"Generate a 7-day health and wealth plan. "
        f"Weekly budget limit is {clean_budget} {clean_currency}. "
        f"Daily nutrition target is {calorie_target} calories. "
        f"Weight Goal target is {clean_goal}. "
        f"Dietary Preferences: {clean_preferences}."
    )

    print("\n[Security Auditor] Inputs sanitized and verified.")
    print(f'[Architect] Initiating dual-agent cascade with prompt:\n"{user_prompt}"\n')
    print("[Developer] Starting ADK engine execution (negotiation & formatting)...")

    # 2. Setup runner
    from app.agent import app as adk_app

    runner = InMemoryRunner(app=adk_app)
    runner.auto_create_session = True
    session_service = runner.session_service

    user_id = "cli_user"
    session_id = "cli_session"

    from google.genai import types

    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])

    # Execute the run_async pipeline
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=new_msg
    ):
        # Print high level events or log changes
        if event.author == "habit_planner_negotiator" and event.content:
            text = ""
            if isinstance(event.content, str):
                text = event.content
            elif hasattr(event.content, "parts") and event.content.parts:
                text = getattr(event.content.parts[0], "text", "") or ""
            print(f"[{event.author}] {text[:150]}...")

    # Load session state to retrieve formatted Pydantic output schema
    session = await session_service.get_session(
        app_name="app", user_id=user_id, session_id=session_id
    )
    strategy = session.state.get("strategy")

    if strategy:
        print("\n==================================================")
        print("=== THE WEALTH-HEALTH STRATEGY MATRIX GENERATED ===")
        print("==================================================")

        # Format output as formatted JSON
        if hasattr(strategy, "model_dump"):
            data_dict = strategy.model_dump()
        else:
            data_dict = strategy

        print(json.dumps(data_dict, indent=2))
        print("==================================================")
        print(
            f"Weekly Total Cost: {data_dict.get('weekly_total_cost')} {data_dict.get('currency')}"
        )
        print(f"Within Budget Limit: {data_dict.get('within_budget_verification')}")
        print("==================================================")
    else:
        print(
            "\n[Error] Strategy could not be synthesized. Please verify Gemini API key configuration."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wealth-Health Strategist AI Agent CLI Runner"
    )
    parser.add_argument(
        "--budget", type=float, default=200.0, help="Weekly grocery budget"
    )
    parser.add_argument(
        "--currency",
        type=str,
        default="USD",
        choices=["USD", "INR"],
        help="Currency (USD/INR)",
    )
    parser.add_argument(
        "--calories", type=float, default=2000.0, help="Daily target calorie count"
    )
    parser.add_argument(
        "--goal",
        type=str,
        default="weight_loss",
        choices=["weight_loss", "muscle_gain", "maintenance"],
        help="Weight Goal",
    )
    parser.add_argument(
        "--preferences",
        type=str,
        default="High protein",
        help="Dietary preferences or constraints",
    )

    args = parser.parse_args()

    asyncio.run(
        run_cli_strategy(
            budget=args.budget,
            currency=args.currency,
            calorie_target=args.calories,
            goal=args.goal,
            preferences=args.preferences,
        )
    )
