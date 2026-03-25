# src/cli/app.py
"""
Main CLI application.
The entry point for the second brain.
"""
import asyncio
import os
import logfire
from rich.prompt import Prompt
from src.cli.display import (
    console, print_welcome, print_help,
    print_divider, print_error, print_info,
    print_success,
)
from src.cli.commands import (
    handle_chat, handle_search, handle_memory,
    handle_remember, handle_profile, handle_ingest,
    handle_stats, handle_eval,
)


class SecondBrainCLI:
    """
    Main CLI application for the second brain.
    Handles command routing and session management.
    """

    def __init__(self):
        self.running = False
        self.messages_log = []  # for memory extraction
        self.session_id = None

    def setup(self):
        """Initialize all systems on startup."""
        console.print("\n[dim]Starting up systems...[/dim]")

        # Setup observability
        logfire.configure(
            service_name="second-brain-cli",
            send_to_logfire=False,
        )
        logfire.instrument_pydantic_ai()

        # Auto-ingest documents on startup
        try:
            from src.rag.document_loader import load_all_documents
            from src.rag.vector_store import vector_store

            docs = load_all_documents()
            if docs:
                added = vector_store.add_documents(docs)
                stats = vector_store.get_stats()
                console.print(
                    f"[dim]📚 Knowledge base: "
                    f"{stats['total_chunks']} chunks loaded[/dim]"
                )
        except Exception as e:
            console.print(f"[dim yellow]⚠️  Could not auto-load docs: {e}[/dim yellow]")

        # Show memory stats
        try:
            from src.memory.memory_store import memory_store
            stats = memory_store.get_stats()
            console.print(
                f"[dim]💾 Memory: {stats['total_memories']} "
                f"memories loaded[/dim]"
            )
        except Exception as e:
            console.print(
                f"[dim yellow]⚠️  Memory store: {e}[/dim yellow]"
            )

        import uuid
        self.session_id = str(uuid.uuid4())
        console.print(
            f"[dim]🔑 Session: {self.session_id[:8]}...[/dim]\n"
        )

    async def end_session(self):
        """Save memories from this session before exiting."""
        if not self.messages_log:
            return

        console.print("\n[dim]💭 Saving session memories...[/dim]")

        try:
            from src.memory.memory_agent import extract_and_save_memories
            from src.memory.memory_store import memory_store
            from src.guardrails.guardrail import pii_guardrail

            conversation = "\n".join(self.messages_log)
            clean_conv = pii_guardrail.process_for_storage(conversation)

            saved = await extract_and_save_memories(clean_conv)

            if saved > 0:
                memory_store.save_conversation_summary(
                    summary=f"Session {self.session_id[:8]}: "
                            f"{self.messages_log[0][:80] if self.messages_log else 'general chat'}",
                    message_count=len(self.messages_log) // 2,
                )
                print_success(f"Saved {saved} memories from this session")

        except Exception as e:
            console.print(f"[dim]Could not save session memories: {e}[/dim]")

    async def route_command(self, user_input: str) -> bool:
        """
        Route user input to the correct handler.
        Returns False to quit, True to continue.
        """
        user_input = user_input.strip()

        if not user_input:
            return True

        # Log the interaction
        logfire.info("cli_command", input=user_input[:50])

        # ── Quit ──────────────────────────────────────────────────
        if user_input.lower() in ["/quit", "/exit", "/q", "quit", "exit"]:
            return False

        # ── Help ──────────────────────────────────────────────────
        elif user_input.lower() in ["/help", "/h", "help"]:
            print_help()

        # ── Clear screen ──────────────────────────────────────────
        elif user_input.lower() == "/clear":
            os.system("clear" if os.name == "posix" else "cls")
            print_welcome()

        # ── Chat (multi-agent) ────────────────────────────────────
        elif user_input.startswith("/chat "):
            message = user_input[6:].strip()
            await handle_chat(message, self)

        # ── Search (RAG only) ─────────────────────────────────────
        elif user_input.startswith("/search "):
            query = user_input[8:].strip()
            await handle_search(query)

        # ── Memory ────────────────────────────────────────────────
        elif user_input.startswith("/memory"):
            args = user_input[7:].strip()
            await handle_memory(args)

        # ── Remember ──────────────────────────────────────────────
        elif user_input.startswith("/remember "):
            content = user_input[10:].strip()
            await handle_remember(content)

        # ── Profile ───────────────────────────────────────────────
        elif user_input.lower() == "/profile":
            await handle_profile()

        # ── Ingest ────────────────────────────────────────────────
        elif user_input.lower() == "/ingest":
            await handle_ingest()

        # ── Stats ─────────────────────────────────────────────────
        elif user_input.lower() == "/stats":
            await handle_stats()

        # ── Eval ──────────────────────────────────────────────────
        elif user_input.lower() == "/eval":
            await handle_eval()

        # ── Plain message (no slash) → treat as chat ──────────────
        elif not user_input.startswith("/"):
            await handle_chat(user_input, self)

        # ── Unknown command ────────────────────────────────────────
        else:
            print_error(
                f"Unknown command: '{user_input}'. "
                f"Type /help to see available commands."
            )

        print_divider()
        return True

    async def run(self):
        """Main application loop."""
        self.running = True
        self.setup()
        print_welcome()

        try:
            while self.running:
                try:
                    # Get user input
                    user_input = Prompt.ask(
                        "\n[bold blue]You[/bold blue]"
                    )

                    should_continue = await self.route_command(user_input)

                    if not should_continue:
                        break

                except KeyboardInterrupt:
                    console.print(
                        "\n[dim]Use /quit to exit[/dim]"
                    )
                    continue

        finally:
            # Always save memories on exit
            await self.end_session()
            console.print(
                "\n[bold blue]👋 Goodbye! Your memories have been saved.[/bold blue]\n"
            )