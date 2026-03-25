# src/cli/commands.py
"""
Command handlers for the CLI.
Each function handles one slash command.
"""
import asyncio
import logfire
from src.cli.display import (
    console, print_answer, print_search_results,
    print_memories, print_stats, print_success,
    print_error, print_info, print_warning,
)


async def handle_chat(message: str, session) -> bool:
    """
    Handle /chat command.
    Uses full multi-agent system.
    """
    if not message.strip():
        print_warning("Please provide a message. Example: /chat What recipes do I have?")
        return True

    with console.status("[bold green]🧠 Thinking...[/bold green]"):
        try:
            from src.agents.orchestrator_agent import orchestrator
            response = await orchestrator.process(message)

            print_answer(
                answer=response.answer,
                metadata={
                    "agents_used": response.agents_used,
                    "sources": response.sources,
                    "confidence": response.confidence,
                    "processing_time_seconds": response.processing_time_seconds,
                    "used_memory": response.used_memory,
                },
            )

            # Auto-save to session for memory extraction later
            if hasattr(session, "messages_log"):
                session.messages_log.append(f"User: {message}")
                session.messages_log.append(f"Assistant: {response.answer}")

        except Exception as e:
            print_error(f"Chat failed: {e}")
            logfire.error("cli_chat_error", error=str(e))

    return True


async def handle_search(query: str) -> bool:
    """
    Handle /search command.
    Direct vector search, no LLM.
    """
    if not query.strip():
        print_warning("Please provide a query. Example: /search pasta recipe")
        return True

    with console.status("[bold cyan]🔍 Searching knowledge base...[/bold cyan]"):
        try:
            from src.rag.vector_store import vector_store
            results = vector_store.search(query, top_k=4)
            print_search_results(results)

        except Exception as e:
            print_error(f"Search failed: {e}")

    return True


async def handle_memory(args: str = "") -> bool:
    """
    Handle /memory command.
    Shows stored memories, optionally filtered.
    """
    try:
        from src.memory.memory_store import memory_store

        if args.strip():
            # Search memories by keyword
            memories = memory_store.search_memories(args.strip())
            print_info(f"Memories matching '{args.strip()}':")
        else:
            # Show all memories
            memories = memory_store.get_all_memories()

        print_memories(memories)

    except Exception as e:
        print_error(f"Memory retrieval failed: {e}")

    return True


async def handle_remember(content: str) -> bool:
    """
    Handle /remember command.
    Manually save a fact to memory.
    """
    if not content.strip():
        print_warning(
            "Please provide content. Example: /remember I prefer concise answers"
        )
        return True

    try:
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType
        from src.guardrails.guardrail import pii_guardrail

        # Clean PII before saving
        clean_content = pii_guardrail.process_for_storage(content)

        memory = memory_store.save_memory(
            content=clean_content,
            memory_type=MemoryType.FACT,
            importance=4,
            tags=["manual", "user-added"],
        )

        print_success(f"Remembered: '{clean_content}'")
        print_info(f"Memory ID: {memory.id[:8]}...")

    except Exception as e:
        print_error(f"Could not save memory: {e}")

    return True


async def handle_profile() -> bool:
    """
    Handle /profile command.
    Shows the user profile.
    """
    try:
        from src.memory.memory_store import memory_store
        profile = memory_store.get_user_profile()

        console.print("\n[bold]👤 Your Profile:[/bold]")
        console.print(f"  Name: {profile.name}")

        if profile.preferences:
            console.print("\n  [cyan]Preferences:[/cyan]")
            for p in profile.preferences:
                console.print(f"    • {p}")

        if profile.known_facts:
            console.print("\n  [cyan]Known Facts:[/cyan]")
            for f in profile.known_facts:
                console.print(f"    • {f}")

        if profile.interests:
            console.print("\n  [cyan]Interests:[/cyan]")
            for i in profile.interests:
                console.print(f"    • {i}")

        console.print(
            f"\n  [dim]Last updated: {profile.last_updated[:10]}[/dim]"
        )

    except Exception as e:
        print_error(f"Profile retrieval failed: {e}")

    return True


async def handle_ingest() -> bool:
    """
    Handle /ingest command.
    Load/reload documents into vector store.
    """
    with console.status(
        "[bold yellow]📚 Loading documents...[/bold yellow]"
    ):
        try:
            from src.rag.document_loader import load_all_documents
            from src.rag.vector_store import vector_store

            documents = load_all_documents()

            if not documents:
                print_warning(
                    "No documents found. Add .md or .txt files to "
                    "data/notes/, data/recipes/, or data/transcriptions/"
                )
                return True

            added = vector_store.add_documents(documents)

            stats = vector_store.get_stats()
            print_success(
                f"Ingested {len(documents)} chunks "
                f"({added} new) from your documents"
            )
            print_info(
                f"Total in knowledge base: {stats['total_chunks']} chunks"
            )

        except Exception as e:
            print_error(f"Ingestion failed: {e}")

    return True


async def handle_stats() -> bool:
    """
    Handle /stats command.
    Show comprehensive system statistics.
    """
    try:
        from src.memory.memory_store import memory_store
        from src.rag.vector_store import vector_store
        from src.observability.metrics import agent_metrics
        from src.guardrails.guardrail import pii_guardrail
        from src.agents.orchestrator_agent import orchestrator

        stats = {
            "Knowledge Base": vector_store.get_stats(),
            "Memory Store": memory_store.get_stats(),
            "Agent Metrics": agent_metrics.summary(),
            "PII Guardrail": pii_guardrail.get_stats(),
            "Orchestrator": orchestrator.get_stats(),
        }

        print_stats(stats)

    except Exception as e:
        print_error(f"Stats retrieval failed: {e}")

    return True


async def handle_eval() -> bool:
    """
    Handle /eval command.
    Run a quick mini evaluation.
    """
    print_info(
        "Running quick evaluation (3 cases each system)...\n"
        "For full eval run: python run_evals.py"
    )

    with console.status("[bold magenta]📊 Evaluating...[/bold magenta]"):
        try:
            from src.evaluation.evaluator import (
                evaluate_system,
                run_baseline,
                run_rag_system,
            )
            from src.evaluation.dataset import (
                BASELINE_EVAL_CASES, RAG_EVAL_CASES
            )

            # Run just 2 cases each for speed
            base = await evaluate_system(
                "Baseline",
                BASELINE_EVAL_CASES[:2],
                run_baseline,
            )
            rag = await evaluate_system(
                "RAG",
                RAG_EVAL_CASES[:2],
                run_rag_system,
            )

            console.print("\n[bold]📊 Quick Eval Results:[/bold]")
            console.print(
                f"  Baseline: score={base.avg_score:.3f} "
                f"pass_rate={base.pass_rate:.0%}"
            )
            console.print(
                f"  RAG:      score={rag.avg_score:.3f} "
                f"pass_rate={rag.pass_rate:.0%}"
            )

            if rag.avg_score > base.avg_score:
                diff = rag.avg_score - base.avg_score
                console.print(
                    f"\n  [green]✅ RAG improves score by "
                    f"{diff:.3f} ({diff/base.avg_score*100:.1f}%)[/green]"
                )
            else:
                console.print(
                    "\n  [yellow]⚠️  Results similar - "
                    "try adding more documents![/yellow]"
                )

        except Exception as e:
            print_error(f"Evaluation failed: {e}")

    return True