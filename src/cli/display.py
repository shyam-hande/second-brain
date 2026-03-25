# src/cli/display.py
"""
Rich-based display helpers for the CLI.
Handles all the pretty printing.
"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.rule import Rule
from rich import box

console = Console()


def print_welcome():
    """Print welcome banner."""
    console.print(Panel(
        "[bold blue]🧠 Second Brain[/bold blue]\n"
        "[dim]Your personal AI-powered knowledge assistant[/dim]\n\n"
        "Type [bold green]/help[/bold green] to see all commands\n"
        "Type [bold green]/quit[/bold green] to exit",
        border_style="blue",
        padding=(1, 4),
    ))


def print_help():
    """Print available commands."""
    table = Table(
        title="Available Commands",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Command", style="bold green", width=20)
    table.add_column("Description", style="white")
    table.add_column("Example", style="dim")

    commands = [
        ("/chat <message>",
         "Chat using full multi-agent system",
         "/chat What recipes do I have?"),
        ("/search <query>",
         "Search knowledge base directly",
         "/search carbonara ingredients"),
        ("/memory",
         "Show stored memories",
         "/memory"),
        ("/remember <fact>",
         "Manually save a memory",
         "/remember I prefer bullet points"),
        ("/profile",
         "Show your user profile",
         "/profile"),
        ("/ingest",
         "Load documents into knowledge base",
         "/ingest"),
        ("/stats",
         "Show system statistics",
         "/stats"),
        ("/eval",
         "Run quick evaluation suite",
         "/eval"),
        ("/clear",
         "Clear the screen",
         "/clear"),
        ("/quit",
         "Exit the second brain",
         "/quit"),
    ]

    for cmd, desc, example in commands:
        table.add_row(cmd, desc, example)

    console.print(table)


def print_answer(answer: str, metadata: dict = None):
    """Print an agent answer with optional metadata."""
    # Print the main answer as markdown
    console.print(Panel(
        Markdown(answer),
        title="[bold green]🧠 Second Brain[/bold green]",
        border_style="green",
        padding=(1, 2),
    ))

    # Print metadata if provided
    if metadata:
        meta_parts = []

        if metadata.get("agents_used"):
            agents = ", ".join(metadata["agents_used"])
            meta_parts.append(f"🤖 Agents: {agents}")

        if metadata.get("sources"):
            sources = ", ".join(metadata["sources"])
            meta_parts.append(f"📁 Sources: {sources}")

        if metadata.get("confidence"):
            meta_parts.append(f"🎯 Confidence: {metadata['confidence']}")

        if metadata.get("processing_time_seconds"):
            meta_parts.append(
                f"⏱️  Time: {metadata['processing_time_seconds']}s"
            )

        if metadata.get("used_memory"):
            meta_parts.append("💾 Used memory: yes")

        if meta_parts:
            console.print(
                "[dim]" + " | ".join(meta_parts) + "[/dim]"
            )


def print_search_results(results: list[dict]):
    """Print vector search results."""
    if not results:
        console.print("[yellow]No results found in knowledge base[/yellow]")
        return

    console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")

    for i, result in enumerate(results, 1):
        filename = result["metadata"].get("filename", "unknown")
        category = result["metadata"].get("category", "")
        score = result["relevance_score"]
        content = result["content"][:200]

        console.print(Panel(
            f"{content}...",
            title=f"[cyan]{i}. {filename}[/cyan] "
                  f"[dim]({category})[/dim] "
                  f"[green]score: {score}[/green]",
            border_style="cyan",
        ))


def print_memories(memories: list):
    """Print stored memories in a table."""
    if not memories:
        console.print("[yellow]No memories stored yet[/yellow]")
        return

    table = Table(
        title=f"💾 Stored Memories ({len(memories)} total)",
        box=box.SIMPLE,
        show_lines=True,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Content", style="white")
    table.add_column("Importance", justify="center", width=10)
    table.add_column("Date", style="dim", width=12)

    for i, memory in enumerate(memories, 1):
        importance_str = "⭐" * memory.importance
        date = memory.created_at[:10] if memory.created_at else "unknown"

        table.add_row(
            str(i),
            memory.type,
            memory.content[:60] + "..." if len(memory.content) > 60
            else memory.content,
            importance_str,
            date,
        )

    console.print(table)


def print_stats(stats: dict):
    """Print system statistics."""
    table = Table(
        title="📊 System Statistics",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Component", style="bold cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold green")

    for section, data in stats.items():
        if isinstance(data, dict):
            for key, value in data.items():
                table.add_row(section, key, str(value))
        else:
            table.add_row(section, "", str(data))

    console.print(table)


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]❌ Error:[/bold red] {message}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]✅[/bold green] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[bold blue]ℹ️ [/bold blue] {message}")


def print_warning(message: str):
    """Print a warning message."""
    console.print(f"[bold yellow]⚠️ [/bold yellow] {message}")


def print_divider():
    """Print a visual divider."""
    console.print(Rule(style="dim"))