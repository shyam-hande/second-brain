# run_evals.py
"""
Main evaluation script.
Runs all three systems and compares them.

This is the EVIDENCE that multi-agent + RAG + memory
actually helps over a simple baseline.
"""
import asyncio
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

import logfire
logfire.configure(service_name="second-brain-evals", send_to_logfire=False)

from src.evaluation.evaluator import (
    evaluate_system,
    run_baseline,
    run_rag_system,
    run_multiagent_system,
)
from src.evaluation.dataset import (
    RAG_EVAL_CASES,
    MULTIAGENT_EVAL_CASES,
    BASELINE_EVAL_CASES,
)
from src.evaluation.models import EvalSummary

console = Console()


def print_comparison_table(summaries: list[EvalSummary]):
    """Print a comparison table of all systems."""

    table = Table(title="📊 System Comparison", show_lines=True)

    table.add_column("System", style="bold cyan")
    table.add_column("Cases", justify="center")
    table.add_column("Pass Rate", justify="center")
    table.add_column("Avg Score", justify="center")
    table.add_column("Avg Latency", justify="center")

    for s in summaries:
        pass_rate_pct = f"{s.pass_rate * 100:.0f}%"
        avg_score_str = f"{s.avg_score:.3f}"
        latency_str = f"{s.avg_latency:.1f}s"

        # Color code the scores
        if s.avg_score >= 0.8:
            score_style = "green"
        elif s.avg_score >= 0.6:
            score_style = "yellow"
        else:
            score_style = "red"

        table.add_row(
            s.system_name,
            str(s.total_cases),
            pass_rate_pct,
            f"[{score_style}]{avg_score_str}[/{score_style}]",
            latency_str,
        )

    console.print(table)


def print_insights(summaries: list[EvalSummary]):
    """Print key insights from the evaluation."""

    console.print("\n[bold]💡 Key Insights:[/bold]")

    baseline = next((s for s in summaries if "Baseline" in s.system_name), None)
    rag = next((s for s in summaries if "RAG" in s.system_name), None)
    ma = next((s for s in summaries if "Multi" in s.system_name), None)

    if baseline and rag:
        diff = rag.avg_score - baseline.avg_score
        pct = (diff / baseline.avg_score * 100) if baseline.avg_score > 0 else 0
        direction = "better" if diff > 0 else "worse"
        console.print(
            f"  📚 RAG is [bold]{abs(pct):.1f}%[/bold] {direction} "
            f"than baseline "
            f"({baseline.avg_score:.3f} → {rag.avg_score:.3f})"
        )

    if baseline and ma:
        diff = ma.avg_score - baseline.avg_score
        pct = (diff / baseline.avg_score * 100) if baseline.avg_score > 0 else 0
        direction = "better" if diff > 0 else "worse"
        console.print(
            f"  🤖 Multi-Agent is [bold]{abs(pct):.1f}%[/bold] {direction} "
            f"than baseline "
            f"({baseline.avg_score:.3f} → {ma.avg_score:.3f})"
        )

    if rag and ma:
        latency_diff = ma.avg_latency - rag.avg_latency
        console.print(
            f"  ⏱️  Multi-Agent is {abs(latency_diff):.1f}s "
            f"{'slower' if latency_diff > 0 else 'faster'} than RAG "
            f"(trade-off for better quality)"
        )


async def main():
    console.print(Panel(
        "🧠 Second Brain - Evaluation Suite\n"
        "Comparing: Baseline vs RAG vs Multi-Agent",
        style="bold blue",
    ))

    summaries = []

    # ── Evaluation 1: Baseline ─────────────────────────────────────
    console.print("\n[bold yellow]Running Baseline Evaluation...[/bold yellow]")
    baseline_summary = await evaluate_system(
        system_name="Baseline (No RAG)",
        cases=BASELINE_EVAL_CASES,
        runner_func=run_baseline,
    )
    summaries.append(baseline_summary)

    # ── Evaluation 2: RAG System ───────────────────────────────────
    console.print("\n[bold yellow]Running RAG Evaluation...[/bold yellow]")
    rag_summary = await evaluate_system(
        system_name="RAG System",
        cases=RAG_EVAL_CASES,
        runner_func=run_rag_system,
    )
    summaries.append(rag_summary)

    # ── Evaluation 3: Multi-Agent System ──────────────────────────
    console.print("\n[bold yellow]Running Multi-Agent Evaluation...[/bold yellow]")
    ma_summary = await evaluate_system(
        system_name="Multi-Agent System",
        cases=MULTIAGENT_EVAL_CASES,
        runner_func=run_multiagent_system,
    )
    summaries.append(ma_summary)

    # ── Print Results ──────────────────────────────────────────────
    console.print("\n")
    print_comparison_table(summaries)
    print_insights(summaries)

    # ── Save Results to JSON ───────────────────────────────────────
    results_file = f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(
            [s.model_dump() for s in summaries],
            f,
            indent=2,
        )
    console.print(f"\n💾 Results saved to: {results_file}")

    # ── Final verdict ──────────────────────────────────────────────
    best = max(summaries, key=lambda s: s.avg_score)
    console.print(Panel(
        f"🏆 Best performing system: [bold green]{best.system_name}[/bold green]\n"
        f"   Score: {best.avg_score:.3f} | Pass rate: {best.pass_rate*100:.0f}%",
        style="green",
    ))


if __name__ == "__main__":
    asyncio.run(main())