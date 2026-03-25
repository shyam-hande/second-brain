# src/memory/memory_store.py
from tinydb import TinyDB, Query
from datetime import datetime
import uuid
import logfire
from src.config import settings
from src.memory.models import Memory, MemoryType, ConversationSummary, UserProfile


class MemoryStore:
    """
    Local persistent memory storage using TinyDB.
    
    TinyDB stores everything as JSON on disk.
    Simple, local, no server needed.
    
    Structure:
        data/memory.json
        ├── memories table     → individual memory units
        ├── conversations table → past conversation summaries  
        └── profile table      → user profile
    """

    def __init__(self):
        self.db = TinyDB(settings.memory_db_path)
        self.memories = self.db.table("memories")
        self.conversations = self.db.table("conversations")
        self.profile = self.db.table("profile")
        logfire.info("memory_store_initialized", path=settings.memory_db_path)
        print(f"✅ Memory store ready at {settings.memory_db_path}")

    # ── MEMORY CRUD ────────────────────────────────────────────────────────────

   # In src/memory/memory_store.py
   # Update the save_memory method only:

    def save_memory(
        self,
        content: str,
        memory_type: MemoryType,
        importance: int = 3,
        tags: list[str] = None,
    ) -> Memory:
        """Save a new memory to the store - with PII protection."""

        # ── Clean PII before storing ───────────────────────────────
        from src.guardrails.guardrail import pii_guardrail
        clean_content = pii_guardrail.process_memory_content(content)

        if clean_content != content:
            logfire.warning(
                "memory_pii_cleaned",
                original_length=len(content),
                cleaned_length=len(clean_content),
            )
        # ──────────────────────────────────────────────────────────

        memory = Memory(
            id=str(uuid.uuid4()),
            type=memory_type,
            content=clean_content,   # store clean version
            importance=importance,
            tags=tags or [],
        )

        self.memories.insert(memory.model_dump())

        logfire.info(
            "memory_saved",
            memory_id=memory.id,
            memory_type=memory_type,
            importance=importance,
        )

        return memory

    def get_all_memories(self) -> list[Memory]:
        """Get all stored memories."""
        records = self.memories.all()
        return [Memory(**r) for r in records]

    def get_memories_by_type(self, memory_type: MemoryType) -> list[Memory]:
        """Get memories filtered by type."""
        MemoryQuery = Query()
        records = self.memories.search(MemoryQuery.type == memory_type.value)
        return [Memory(**r) for r in records]

    def search_memories(self, keyword: str) -> list[Memory]:
        """
        Simple keyword search through memories.
        (For semantic search we would use ChromaDB,
         but keyword is fine for memories)
        """
        keyword_lower = keyword.lower()
        MemoryQuery = Query()
        records = self.memories.search(
            MemoryQuery.content.test(
                lambda content: keyword_lower in content.lower()
            )
        )

        # Update access count and last_accessed
        for record in records:
            self.memories.update(
                {
                    "access_count": record.get("access_count", 0) + 1,
                    "last_accessed": datetime.now().isoformat(),
                },
                MemoryQuery.id == record["id"],
            )

        return [Memory(**r) for r in records]

    def get_important_memories(self, min_importance: int = 4) -> list[Memory]:
        """Get high importance memories."""
        MemoryQuery = Query()
        records = self.memories.search(
            MemoryQuery.importance >= min_importance
        )
        # Sort by importance descending
        records.sort(key=lambda x: x["importance"], reverse=True)
        return [Memory(**r) for r in records]

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        MemoryQuery = Query()
        removed = self.memories.remove(MemoryQuery.id == memory_id)
        return len(removed) > 0

    # ── CONVERSATION SUMMARIES ─────────────────────────────────────────────────

    def save_conversation_summary(
        self,
        summary: str,
        key_topics: list[str] = None,
        message_count: int = 0,
    ) -> ConversationSummary:
        """Save a summary of a completed conversation."""

        conv = ConversationSummary(
            session_id=str(uuid.uuid4()),
            summary=summary,
            key_topics=key_topics or [],
            message_count=message_count,
        )

        self.conversations.insert(conv.model_dump())
        logfire.info(
            "conversation_summary_saved",
            session_id=conv.session_id,
            topics=key_topics,
        )

        return conv

    def get_recent_conversations(self, limit: int = 5) -> list[ConversationSummary]:
        """Get most recent conversation summaries."""
        all_convs = self.conversations.all()
        # Sort by created_at descending
        all_convs.sort(key=lambda x: x["created_at"], reverse=True)
        recent = all_convs[:limit]
        return [ConversationSummary(**c) for c in recent]

    # ── USER PROFILE ───────────────────────────────────────────────────────────

    def save_user_profile(self, profile: UserProfile):
        """Save or update the user profile."""
        self.profile.truncate()  # only one profile
        self.profile.insert(profile.model_dump())
        logfire.info("user_profile_saved", name=profile.name)

    def get_user_profile(self) -> UserProfile:
        """Get the user profile, or default if not set."""
        records = self.profile.all()
        if records:
            return UserProfile(**records[0])
        return UserProfile()  # default empty profile

    def update_user_profile(self, **kwargs):
        """Update specific fields of user profile."""
        profile = self.get_user_profile()
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.last_updated = datetime.now().isoformat()
        self.save_user_profile(profile)

    # ── STATS ──────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get memory store statistics."""
        all_memories = self.get_all_memories()
        type_counts = {}
        for m in all_memories:
            type_counts[m.type] = type_counts.get(m.type, 0) + 1

        return {
            "total_memories": len(all_memories),
            "total_conversations": len(self.conversations.all()),
            "memory_types": type_counts,
            "has_profile": len(self.profile.all()) > 0,
        }

    def clear_all(self):
        """Clear everything - use with caution!"""
        self.memories.truncate()
        self.conversations.truncate()
        self.profile.truncate()
        print("🗑️  All memories cleared")


# Global instance
memory_store = MemoryStore()