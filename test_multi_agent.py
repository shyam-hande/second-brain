# test_multiagent.py
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.agents.orchestrator_agent import orchestrator, FinalResponse

console = Console()


def display_response(query: str, response: FinalResponse):
    """Pretty print the response."""
    console.print(f"\n[bold blue]❓ Query:[/bold blue] {query}")

    # Main answer
    console.print(Panel(
        response.answer,
        title="💬 Answer",
        border_style="green",
    ))

    # Key points
    if response.key_points:
        console.print("[bold]📌 Key Points:[/bold]")
        for point in response.key_points:
            console.print(f"  • {point}")

    # Metadata table
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("🤖 Agents used", ", ".join(response.agents_used))
    table.add_row("📁 Sources", ", ".join(response.sources) or "none")
    table.add_row("🎯 Confidence", response.confidence)
    table.add_row("📚 Used knowledge base", str(response.used_knowledge_base))
    table.add_row("💾 Used memory", str(response.used_memory))
    table.add_row("⏱️  Time", f"{response.processing_time_seconds}s")
    console.print(table)

    # Follow-ups
    if response.follow_up_suggestions:
        console.print("[bold]💡 Follow-up suggestions:[/bold]")
        for suggestion in response.follow_up_suggestions:
            console.print(f"  → {suggestion}")

    console.print("─" * 60)


async def main():
    console.print(Panel(
        "🧠 Multi-Agent Second Brain System",
        style="bold blue",
    ))

    # Test queries - mix of types
    queries = [
        # Should use research agent (knowledge base)
        "What ingredients do I need for carbonara?",

        # Should use research agent (knowledge base)
        "What Python tips do I have about list comprehensions?",

        # Should use memory agent (personal)
        "What do you know about me?",

        # General query - synthesis only
        "What is the benefit of having a second brain?",
    ]

    for query in queries:
        response = await orchestrator.process(query)
        display_response(query, response)
        # Small delay between calls
        await asyncio.sleep(1)

    # Show overall stats
    stats = orchestrator.get_stats()
    console.print(Panel(
        f"Total queries: {stats['total_queries']}\n"
        f"Total time: {stats['total_time_seconds']}s\n"
        f"Avg time per query: {stats['avg_time_seconds']}s",
        title="📊 Orchestrator Stats",
        style="yellow",
    ))


if __name__ == "__main__":
    asyncio.run(main())