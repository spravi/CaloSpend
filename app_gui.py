# app_gui.py
import logging

from dotenv import load_dotenv

load_dotenv()  # Load env vars from .env file

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Import ADK core runner and agent
from google.adk.runners import InMemoryRunner
from pydantic import BaseModel

from app.agent import app as adk_app

# Import security sanitizers
from app.security import sanitize_budget, sanitize_input_text

# Initialize FastAPI
app = FastAPI(title="The Wealth-Health Strategist Dashboard")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WealthHealthGUI")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Initialize the ADK stateful runner
runner = InMemoryRunner(app=adk_app)
runner.auto_create_session = True
session_service = runner.session_service


class StrategyRequest(BaseModel):
    budget: float
    currency: str
    calorie_target: float
    goal: str
    preferences: str


@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """Serves the main interactive dashboard UI."""
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/generate-strategy")
async def generate_strategy_api(payload: StrategyRequest):
    """Receives user input, sanitizes it, runs ADK agent cascade, and returns structured data."""

    # 1. Day 4 Input Sanitization & Safety Guardrails
    clean_goal = sanitize_input_text(payload.goal)
    clean_preferences = sanitize_input_text(payload.preferences)
    clean_budget = sanitize_budget(payload.budget)
    clean_currency = "INR" if payload.currency.upper() == "INR" else "USD"
    clean_calorie = max(800.0, min(float(payload.calorie_target), 5000.0))

    # Construct clean prompt
    user_prompt = (
        f"Generate a 7-day health and wealth plan. "
        f"Weekly budget limit is {clean_budget} {clean_currency}. "
        f"Daily nutrition target is {clean_calorie} calories. "
        f"Weight Goal target is {clean_goal}. "
        f"Dietary Preferences: {clean_preferences}."
    )

    logger.info("Executing Agent run with sanitized prompt: %s", user_prompt)

    # 2. Asynchronous ADK Core Execution wrapped in Security audits
    async def run_agent_pipeline():
        user_id = "default_user_1"
        session_id = "health_wealth_session"

        # Clear existing session first to ensure clean state and fresh calculations
        try:
            await session_service.delete_session(
                app_name="app", user_id=user_id, session_id=session_id
            )
        except Exception:
            pass  # Session might not exist yet

        from google.genai import types

        new_msg = types.Content(
            role="user", parts=[types.Part.from_text(text=user_prompt)]
        )

        # Run the sequential agents
        async for _ in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=new_msg
        ):
            pass

        # Load session state to retrieve Pydantic strategy schema
        session = await session_service.get_session(
            app_name="app", user_id=user_id, session_id=session_id
        )
        strategy = session.state.get("strategy")
        if not strategy:
            raise ValueError(
                "Agent failed to output a formatted strategy. Check core model settings."
            )

        # Return serializable dict representation
        if hasattr(strategy, "model_dump"):
            return strategy.model_dump()
        return strategy

    # Executing using safety wrap to protect against credential leaks
    execution_result = await execute_with_safety_guard_async(run_agent_pipeline)

    if execution_result["status"] == "success":
        return execution_result
    else:
        logger.error("Agent execution failed: %s", execution_result.get("error"))
        raise HTTPException(status_code=500, detail=execution_result.get("error"))


async def execute_with_safety_guard_async(coro):
    """Helper to wrap async function execution with safety guards."""
    try:
        data = await coro()
        return {"status": "success", "data": data}
    except Exception as e:
        logger.exception("Raw exception intercepted:")
        return {"status": "failed", "error": str(e)}
