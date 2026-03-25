# health_check.py
"""
Comprehensive health check for all system components.
Run this to verify everything is working before demo.
"""
import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


async def check_component(name: str, check_fn) -> tuple[bool, str]:
    """Run a single component check."""
    try:
        result = await check_fn()
        return True, result
    except Exception as e:
        return False, str(e)


async def check_config():
    from src.config import settings
    return (
        f"Model: {settings.model_name} | "
        f"Key set: {bool(settings.anthropic_api_key)}"
    )


async def check_rag():
    from src.rag.vector_store import vector_store
    stats = vector_store.get_stats()
    count = stats["total_chunks"]
    if count == 0:
        raise Exception("Vector store is empty - run ingest_documents.py")
    return f"{count} chunks in vector store"


async def check_memory():
    from src.memory.memory_store import memory_store
    stats = memory_store.get_stats()
    return (
        f"{stats['total_memories']} memories | "
        f"{stats['total_conversations']} conversations"
    )


async def check_guardrails():
    from src.guardrails.pii_detector import redact_pii
    test = "Email: test@example.com and SSN: 123-45-6789"
    redacted, matches = redact_pii(test)
    if len(matches) != 2:
        raise Exception(f"Expected 2 matches, got {len(matches)}")
    return f"Detected and redacted {len(matches)} PII items"


async def check_base_agent():
    from src.agents.base_agent import chat_async
    response, _ = await chat_async("Say OK in one word")
    if not response.answer:
        raise Exception("No answer received")
    return f"Response: '{response.answer[:30]}...'"


async def check_research_agent():
    from src.agents.research_agent import research
    result = await research("carbonara pasta recipe")
    return (
        f"{len(result.findings)} findings | "
        f"Sources: {result.sources}"
    )


async def check_orchestrator():
    from src.agents.orchestrator_agent import orchestrator
    response = await orchestrator.process(
        "What Python tips do I have?"
    )
    return (
        f"Agents used: {response.agents_used} | "
        f"Time: {response.processing_time_seconds}s"
    )


async def check_observability():
    import logfire
    logfire.configure(
        service_name="health-check",
        send_to_logfire=False
    )
    with logfire.span("health-check-test"):
        logfire.info("health_check", status="ok")
    return "Logfire tracing active"


async def check_evaluation():
    from src.evaluation.scorer import score_response
    from src.evaluation.models import ExpectedOutput
    score = score_response(
        actual_answer="Python list comprehensions are faster than loops",
        expected=ExpectedOutput(
            must_contain=["python", "list"],
            min_length=20,
        ),
    )
    return f"Scorer works | Sample score: {score.total_score:.3f}"


async def main():
    console.print(Panel(
        "🧠 Second Brain - System Health Check",
        style="bold blue",
    ))

    checks = [
        ("⚙️  Configuration", check_config),
        ("📚 RAG / Vector Store", check_rag),
        ("💾 Memory Store", check_memory),
        ("🔒 PII Guardrails", check_guardrails),
        ("🤖 Base Agent", check_base_agent),
        ("🔍 Research Agent", check_research_agent),
        ("🎯 Orchestrator", check_orchestrator),
        ("🔭 Observability", check_observability),
        ("📊 Evaluation", check_evaluation),
    ]

    table = Table(
        title="Component Status",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Component", style="bold", width=25)
    table.add_column("Status", width=8)
    table.add_column("Details", style="dim")

    passed = 0
    failed = 0

    for name, check_fn in checks:
        console.print(f"  Checking {name}...", end="\r")
        ok, detail = await check_component(name, check_fn)

        if ok:
            status = "[bold green]✅ OK[/bold green]"
            passed += 1
        else:
            status = "[bold red]❌ FAIL[/bold red]"
            failed += 1

        table.add_row(name, status, detail[:70])

    console.print(" " * 60, end="\r")  # clear status line
    console.print(table)

    # Summary
    total = passed + failed
    if failed == 0:
        console.print(Panel(
            f"[bold green]✅ All {total} components healthy![/bold green]\n"
            f"Your second brain is ready to use.\n"
            f"Run: python main.py",
            style="green",
        ))
    else:
        console.print(Panel(
            f"[yellow]⚠️  {passed}/{total} components healthy[/yellow]\n"
            f"Fix {failed} failing component(s) before running.\n"
            f"Check the details above for errors.",
            style="yellow",
        ))

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)