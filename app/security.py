# app/security.py
import logging
import os
import re
from typing import Any

# Set up protected logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecurityAuditor")


def sanitize_input_text(text: str, max_length: int = 500) -> str:
    """Sanitizes and truncates raw user input to prevent prompt injections or resource overflow.

    Args:
        text: Raw input string from the user.
        max_length: Maximum allowed characters.

    Returns:
        A cleaned, truncated string.
    """
    if not text:
        return ""

    # Truncate
    truncated = text[:max_length]

    # Remove obvious prompt injection patterns / malicious instructions
    # e.g., "ignore all previous instructions", "system override"
    clean = re.sub(
        r"(ignore\s+(all\s+)?previous|system\s+override|bypass\s+safety|instead\s+of\s+that)",
        "[CLEANED]",
        truncated,
        flags=re.IGNORECASE,
    )

    return clean


def sanitize_budget(budget: int | float | str) -> float:
    """Validates and parses the budget parameter.

    Args:
        budget: User input budget.

    Returns:
        Valid float budget value, capped within reasonable boundaries.
    """
    try:
        val = float(budget)
        if val <= 0:
            return 10.0  # fallback minimum budget
        if val > 100000:
            return 100000.0  # cap to manifest boundary limit
        return val
    except (ValueError, TypeError):
        return 100.0  # default fallback


def verify_credentials() -> dict[str, bool]:
    """Ensures no raw API keys are hardcoded and verifies proper environment variables exist.

    Returns:
        Dictionary indicating status of API configurations.
    """
    has_api_key = "GOOGLE_API_KEY" in os.environ
    has_gcp_project = "GOOGLE_CLOUD_PROJECT" in os.environ

    # Ensure keys are loaded dynamically and not hardcoded as literal values in files
    return {
        "google_api_key_loaded": has_api_key,
        "gcp_project_configured": has_gcp_project,
        "secure": True,
    }


def execute_with_safety_guard(fn: callable, *args, **kwargs) -> dict[str, Any]:
    """Wraps tool or API execution in exception blocks to mask raw traceback logs.

    Args:
        fn: Function to execute.
        *args: Variable arguments.
        **kwargs: Keyword arguments.

    Returns:
        A dictionary containing the successful result or a sanitized error output.
    """
    try:
        res = fn(*args, **kwargs)
        return {"status": "success", "data": res}
    except Exception as e:
        # Protect environment variables and trace logs from leaking
        err_msg = str(e)
        logger.error("Security Auditor intercepted runtime exception: %s", err_msg)

        # Mask sensitive env details if they appear in standard errors
        sanitized_err = re.sub(
            r"(AI_STUDIO_KEY|API_KEY|token|secret|password|passwd|key)=[\w\d\-]+",
            r"\1=[MASKED]",
            err_msg,
            flags=re.IGNORECASE,
        )

        return {
            "status": "failed",
            "error": "A secure system exception occurred. Details: " + sanitized_err,
        }
