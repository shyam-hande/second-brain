# src/memory/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """Types of memories we can store."""
    PREFERENCE = "preference"   # e.g. "user likes concise answers"
    FACT = "fact"               # e.g. "user is learning Python"
    CONVERSATION = "conversation"  # e.g. summary of past conversation
    CONTEXT = "context"         # e.g. "user is working on second brain project"


class Memory(BaseModel):
    """A single memory unit."""
    id: str
    type: MemoryType
    content: str                # the actual memory text
    importance: int = Field(    # 1=low, 5=high
        default=3,
        ge=1,
        le=5
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    last_accessed: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    access_count: int = 0
    tags: list[str] = []


class ConversationSummary(BaseModel):
    """Summary of a past conversation session."""
    session_id: str
    summary: str
    key_topics: list[str] = []
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    message_count: int = 0


class UserProfile(BaseModel):
    """Persistent user profile built from memories."""
    name: str = "User"
    preferences: list[str] = []
    known_facts: list[str] = []
    interests: list[str] = []
    last_updated: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )