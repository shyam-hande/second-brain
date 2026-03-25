# src/observability/tracer.py
import logfire
from src.config import settings


def setup_observability(service_name: str = "second-brain"):
    """
    Configure Logfire for local observability.
    This sets up tracing for all pydantic-ai agent calls.
    """
    logfire.configure(
        service_name=service_name,
        # Send to logfire cloud OR just console
        # We use console for local dev - no account needed!
        send_to_logfire=False,
    )

    # This single line instruments ALL pydantic-ai agents automatically
    logfire.instrument_pydantic_ai()

    print(f"✅ Observability configured for: {service_name}")
    return logfire