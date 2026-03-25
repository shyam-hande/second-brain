# src/memory/session.py
import asyncio
import uuid
import logfire
from src.memory.memory_store import memory_store
from src.memory.memory_agent import extract_and_save_memories
from src.memory.models import MemoryType
from src.guardrails.guardrail import pii_guardrail  # ← add this


class ChatSession:
    """
    Manages a full conversation session with memory and guardrails.
    """

    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.history = []
        self.messages_log = []
        self.use_rag = True

    async def chat(self, message: str) -> str:
        """
        Send a message and get a response.
        Applies PII guardrail on input before anything else.
        """
        with logfire.span("session_chat", session_id=self.session_id):

            # ── Step 1: Guardrail on input ─────────────────────────
            clean_message, was_modified = pii_guardrail.process_input(message)

            if was_modified:
                print("  🔒 Message was cleaned before processing")
            # ───────────────────────────────────────────────────────

            if self.use_rag:
                from src.rag.rag_agent import rag_chat
                response, self.history = await rag_chat(
                    clean_message,
                    history=self.history,
                )
                answer = response.answer
            else:
                from src.agents.base_agent import chat_async
                response, self.history = await chat_async(
                    clean_message,
                    history=self.history,
                )
                answer = response.answer

            # Log clean version for memory extraction
            self.messages_log.append(f"User: {clean_message}")
            self.messages_log.append(f"Assistant: {answer}")

            return answer

    async def end_session(self):
        """End session - extract memories from clean conversation."""
        if not self.messages_log:
            return

        print("\n💭 Processing memories from this conversation...")

        # Conversation is already clean (PII removed at input)
        conversation_text = "\n".join(self.messages_log)

        # Extra safety - clean again before memory extraction
        clean_conversation = pii_guardrail.process_for_storage(
            conversation_text
        )

        memories_saved = await extract_and_save_memories(clean_conversation)
        print(f"  ✅ Saved {memories_saved} new memories")

        if len(self.messages_log) >= 2:
            first_msg = self.messages_log[0].replace("User: ", "")
            summary = f"Conversation about: {first_msg[:100]}"

            # Clean summary before storing
            clean_summary = pii_guardrail.process_for_storage(summary)

            memory_store.save_conversation_summary(
                summary=clean_summary,
                message_count=len(self.messages_log) // 2,
            )
            print(f"  ✅ Conversation summary saved")

        stats = memory_store.get_stats()
        guardrail_stats = pii_guardrail.get_stats()

        print(f"  📊 Memories stored: {stats['total_memories']}")
        print(f"  🔒 PII items redacted this session: "
              f"{guardrail_stats['total_pii_items_redacted']}")