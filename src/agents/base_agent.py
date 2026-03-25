# src/agents/base_agent.py
from pydantic_ai import Agent
from pydantic import BaseModel
from src.config import settings
import asyncio
import logfire
import os

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

# Setup observability
logfire.configure(
    service_name="second-brain",
    send_to_logfire=False,
)
logfire.instrument_pydantic_ai()


class AgentResponse(BaseModel):
    answer: str
    confidence: str
    sources_used: list[str] = []


base_agent = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are a helpful personal assistant and second brain.

    Your job is to:
    - Answer questions clearly and concisely
    - Help the user think through problems
    - Remember context within a conversation
    - Be honest when you don't know something

    Always be conversational but precise.
    When confidence is high, say so. When guessing, say so.
    
    If memory context is provided at the start of the message 
    under [MEMORY CONTEXT], use it to personalize your response.
    """,
    output_type=AgentResponse,
)


async def chat_async(
    message: str,
    history=None,
    use_memory: bool = True,
) -> tuple:
    """
    Async chat with optional memory context injection.
    """
    import time
    start_time = time.time()

    with logfire.span("chat_async", message=message):
        # Inject memory context if enabled
        if use_memory:
            from src.memory.memory_agent import build_memory_context
            memory_context = build_memory_context()

            if memory_context:
                full_message = f"""[MEMORY CONTEXT]
{memory_context}
[END MEMORY CONTEXT]

{message}"""
            else:
                full_message = message
        else:
            full_message = message

        result = await base_agent.run(
            full_message,
            message_history=history or [],
        )

        duration = time.time() - start_time

        # Record metrics
        from src.observability.metrics import agent_metrics
        agent_metrics.record_call(
            duration_seconds=duration,
            confidence=result.output.confidence,
        )

        return result.output, result.new_messages()


def chat(message: str, history=None, use_memory: bool = True):
    """Synchronous wrapper."""
    return asyncio.run(chat_async(message, history, use_memory))