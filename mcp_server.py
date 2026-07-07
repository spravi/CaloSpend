# mcp_server.py
from dotenv import load_dotenv

load_dotenv()  # Load env vars from .env file

from google.adk.runners import InMemoryRunner
from google.genai import types
from mcp.server.fastmcp import FastMCP

# Import the initialized ADK app from the agent component
from app.agent import app as adk_app

# Create a FastMCP server instance
mcp = FastMCP("WealthHealthStrategist")


@mcp.tool()
async def generate_strategy(
    budget: float, currency: str, calorie_target: float, goal: str, preferences: str
) -> str:
    """Generate a 7-day health and wealth plan based on budget, calories, and goals.

    Args:
        budget: Weekly budget limit (e.g. 15.0 or 2000.0)
        currency: The currency to use ('USD' or 'INR')
        calorie_target: Daily calorie intake target (e.g. 2000)
        goal: Weight goal target ('weight_loss', 'muscle_gain', 'maintenance')
        preferences: Dietary preference profile (e.g. 'Standard', 'Pure Vegetarian', 'Vegan')
    """
    # Create an independent local runner instance
    runner = InMemoryRunner(app=adk_app)
    runner.auto_create_session = True

    # Construct the instruction prompt injection
    prompt = f"Generate a 7-day health and wealth plan. Weekly budget limit is {budget} {currency}. Daily nutrition target is {calorie_target} calories. Weight Goal target is {goal}. Dietary Preferences: {preferences}."

    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    # Execute the sequential agents
    async for _ in runner.run_async(
        user_id="mcp_user", session_id="mcp_session", new_message=new_msg
    ):
        pass

    # Retrieve the state after execution
    session = await runner.session_service.get_session(
        app_name="app", user_id="mcp_user", session_id="mcp_session"
    )
    strategy = session.state.get("strategy")

    if strategy:
        import json

        if hasattr(strategy, "model_dump"):
            return json.dumps(strategy.model_dump(), indent=2)
        return json.dumps(strategy, indent=2)
    return "Error: Agent failed to generate strategy."


if __name__ == "__main__":
    # Start the MCP server (supports Stdio by default)
    mcp.run()
