# src/agents/synthesis_agent.py
"""
Synthesis Agent - takes research findings and memory context,
combines them into a clear, personalized final answer.
"""
from pydantic_ai import Agent
from pydantic import BaseModel
from src.config import settings
import logfire
import os

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class SynthesisResult(BaseModel):
    """What the synthesis agent returns."""
    final_answer: str           # the complete answer for the user
    key_points: list[str]       # bullet point summary
    confidence: str             # high / medium / low
    used_knowledge_base: bool   # was RAG used?
    used_memory: bool           # was personal memory used?
    follow_up_suggestions: list[str] = []  # optional follow-ups


synthesis_agent = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are a synthesis specialist for a personal second brain.

    Your job is to:
    1. Take research findings from the knowledge base
    2. Take personal memory context about the user
    3. Combine everything into one clear, helpful answer
    4. Personalize the answer based on what you know about the user

    Rules:
    - Be concise but complete
    - Personalize using memory context if available
    - Clearly separate what comes from documents vs general knowledge
    - Suggest relevant follow-up questions when appropriate
    - Match the user's preferred communication style if known
    """,
    output_type=SynthesisResult,
)


async def synthesize(
    original_query: str,
    research_findings: list[str],
    research_sources: list[str],
    memory_context: str,
    has_knowledge_base_info: bool,
) -> SynthesisResult:
    """
    Synthesize research findings + memory into final answer.
    """
    with logfire.span("synthesis_agent", query=original_query):

        # Build the synthesis prompt
        findings_text = (
            "\n".join(f"- {f}" for f in research_findings)
            if research_findings
            else "No specific findings from knowledge base."
        )

        sources_text = (
            ", ".join(research_sources)
            if research_sources
            else "No sources"
        )

        prompt = f"""
Original Question: {original_query}

Research Findings from Knowledge Base:
{findings_text}

Sources Used: {sources_text}

Personal Memory Context:
{memory_context if memory_context else "No personal memory available."}

Please synthesize this into a helpful, personalized answer.
"""

        result = await synthesis_agent.run(prompt)
        response = result.output
        response.used_knowledge_base = has_knowledge_base_info
        response.used_memory = bool(memory_context)

        logfire.info(
            "synthesis_completed",
            query=original_query,
            used_kb=response.used_knowledge_base,
            used_memory=response.used_memory,
            key_points_count=len(response.key_points),
        )

        return response