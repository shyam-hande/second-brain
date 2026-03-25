# src/memory/memory_agent.py
from pydantic_ai import Agent
from pydantic import BaseModel
from src.config import settings
from src.memory.memory_store import memory_store
from src.memory.models import MemoryType
import logfire
import os

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


# ── What the memory extractor returns ─────────────────────────────────────────
class ExtractedMemories(BaseModel):
    """Memories extracted from a conversation."""
    preferences: list[str] = []   # things user prefers
    facts: list[str] = []         # facts about the user
    interests: list[str] = []     # topics user is interested in
    important_context: list[str] = []  # important context to remember


# ── Memory extraction agent ────────────────────────────────────────────────────
memory_extractor = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are a memory extraction specialist.
    
    Your job is to analyze conversations and extract:
    1. User PREFERENCES (how they like things done)
    2. User FACTS (personal facts about them)  
    3. User INTERESTS (topics they care about)
    4. Important CONTEXT (project details, goals)
    
    Rules:
    - Only extract clearly stated information
    - Be specific, not vague
    - If nothing to extract, return empty lists
    - Keep each memory as one clear sentence
    
    Examples of good memories:
    - "User prefers concise answers without unnecessary detail"
    - "User is building a second brain project in Python"
    - "User is interested in Italian cooking"
    - "User is using Python 3.14 on a Mac"
    """,
    output_type=ExtractedMemories,
)


async def extract_and_save_memories(conversation_text: str) -> int:
    """
    Extract memories from conversation text and save them.
    Returns the number of memories saved.
    """
    if not conversation_text.strip():
        return 0

    with logfire.span("extract_memories"):
        result = await memory_extractor.run(
            f"Extract memories from this conversation:\n\n{conversation_text}"
        )

        extracted = result.output
        saved_count = 0

        # Save preferences
        for pref in extracted.preferences:
            memory_store.save_memory(
                content=pref,
                memory_type=MemoryType.PREFERENCE,
                importance=4,
                tags=["preference"],
            )
            saved_count += 1

        # Save facts
        for fact in extracted.facts:
            memory_store.save_memory(
                content=fact,
                memory_type=MemoryType.FACT,
                importance=3,
                tags=["fact"],
            )
            saved_count += 1

        # Save interests
        for interest in extracted.interests:
            memory_store.save_memory(
                content=interest,
                memory_type=MemoryType.FACT,
                importance=3,
                tags=["interest"],
            )
            saved_count += 1

        # Save important context
        for context in extracted.important_context:
            memory_store.save_memory(
                content=context,
                memory_type=MemoryType.CONTEXT,
                importance=5,
                tags=["context"],
            )
            saved_count += 1

        logfire.info("memories_extracted", count=saved_count)
        return saved_count


def build_memory_context() -> str:
    """
    Build a context string from stored memories.
    This gets injected into agent prompts so it
    'remembers' things about you.
    """
    context_parts = []

    # Get user profile
    profile = memory_store.get_user_profile()
    if profile.name != "User":
        context_parts.append(f"User's name: {profile.name}")

    # Get high importance memories
    important = memory_store.get_important_memories(min_importance=4)
    if important:
        context_parts.append("\nImportant things to remember:")
        for m in important[:5]:  # top 5
            context_parts.append(f"  - {m.content}")

    # Get preferences
    prefs = memory_store.get_memories_by_type(MemoryType.PREFERENCE)
    if prefs:
        context_parts.append("\nUser preferences:")
        for p in prefs[:3]:  # top 3
            context_parts.append(f"  - {p.content}")

    # Get recent conversation summaries
    recent_convs = memory_store.get_recent_conversations(limit=2)
    if recent_convs:
        context_parts.append("\nRecent conversation topics:")
        for conv in recent_convs:
            context_parts.append(f"  - {conv.summary[:100]}")

    return "\n".join(context_parts)