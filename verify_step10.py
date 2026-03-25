# verify_step10.py
"""
Final end-to-end verification of the complete system.
Tests the entire pipeline from CLI to agent to storage.
"""
import asyncio
from rich.console import Console
from rich.panel import Panel

console = Console()


async def verify():
    console.print(Panel(
        "🧠 STEP 10 - FINAL VERIFICATION\n"
        "End-to-end system check",
        style="bold blue",
    ))

    all_good = True
    results = []

    async def check(name: str, fn):
        nonlocal all_good
        try:
            detail = await fn()
            results.append((name, True, detail))
            console.print(f"  ✅ {name}: {detail}")
            return True
        except Exception as e:
            results.append((name, False, str(e)))
            console.print(f"  ❌ {name}: {e}")
            all_good = False
            return False

    # ── 1. Configuration ──────────────────────────────────────────
    console.print("\n[bold]1. Configuration[/bold]")

    async def check_config():
        from src.config import settings
        assert settings.anthropic_api_key
        assert settings.model_name
        return f"Model: {settings.model_name}"

    await check("Settings loaded", check_config)

    # ── 2. Document ingestion ─────────────────────────────────────
    console.print("\n[bold]2. RAG System[/bold]")

    async def check_ingestion():
        from src.rag.document_loader import load_all_documents
        docs = load_all_documents()
        assert len(docs) > 0, "No documents loaded"
        return f"{len(docs)} chunks loaded"

    async def check_vector_store():
        from src.rag.vector_store import vector_store
        stats = vector_store.get_stats()
        assert stats["total_chunks"] > 0
        results_found = vector_store.search("pasta", top_k=2)
        assert len(results_found) > 0
        return f"{stats['total_chunks']} chunks, search works"

    async def check_rag_agent():
        from src.rag.rag_agent import rag_chat
        resp, _ = await rag_chat("What pasta recipes do I have?")
        assert resp.answer
        return f"RAG answered, sources: {resp.sources}"

    await check("Document loading", check_ingestion)
    await check("Vector store", check_vector_store)
    await check("RAG agent", check_rag_agent)

    # ── 3. Memory system ──────────────────────────────────────────
    console.print("\n[bold]3. Memory System[/bold]")

    async def check_memory_save():
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType
        m = memory_store.save_memory(
            "Final verification test memory",
            MemoryType.FACT,
            importance=3,
        )
        assert m.id
        return f"Saved memory {m.id[:8]}..."

    async def check_memory_retrieve():
        from src.memory.memory_store import memory_store
        memories = memory_store.get_all_memories()
        assert len(memories) > 0
        stats = memory_store.get_stats()
        return f"{stats['total_memories']} memories stored"

    async def check_memory_context():
        from src.memory.memory_agent import build_memory_context
        context = build_memory_context()
        return f"Context: {len(context)} chars built"

    await check("Memory save", check_memory_save)
    await check("Memory retrieve", check_memory_retrieve)
    await check("Memory context", check_memory_context)

    # ── 4. PII Guardrails ─────────────────────────────────────────
    console.print("\n[bold]4. PII Guardrails[/bold]")

    async def check_pii_detection():
        from src.guardrails.pii_detector import detect_pii
        matches = detect_pii("john@example.com and 123-45-6789")
        assert len(matches) == 2
        return f"Detected {len(matches)} PII items"

    async def check_pii_redaction():
        from src.guardrails.guardrail import pii_guardrail
        cleaned, modified = pii_guardrail.process_input(
            "Call me at 555-123-4567"
        )
        assert modified
        assert "555-123-4567" not in cleaned
        return "Phone number successfully redacted"

    async def check_memory_pii():
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType
        m = memory_store.save_memory(
            "Contact at test@pii-test.com",
            MemoryType.FACT,
        )
        all_mem = memory_store.get_all_memories()
        saved = next((x for x in all_mem if x.id == m.id), None)
        assert saved
        assert "test@pii-test.com" not in saved.content
        return "PII removed from stored memory"

    await check("PII detection", check_pii_detection)
    await check("PII redaction", check_pii_redaction)
    await check("Memory PII protection", check_memory_pii)

    # ── 5. Multi-Agent System ─────────────────────────────────────
    console.print("\n[bold]5. Multi-Agent System[/bold]")

    async def check_research_agent():
        from src.agents.research_agent import research
        result = await research("carbonara recipe ingredients")
        assert result.findings is not None
        return f"{len(result.findings)} findings, sources: {result.sources}"

    async def check_synthesis_agent():
        from src.agents.synthesis_agent import synthesize
        result = await synthesize(
            original_query="test query",
            research_findings=["fact one", "fact two"],
            research_sources=["test.md"],
            memory_context="user likes concise answers",
            has_knowledge_base_info=True,
        )
        assert result.final_answer
        return f"Synthesized {len(result.final_answer)} char answer"

    async def check_orchestrator():
        from src.agents.orchestrator_agent import orchestrator
        response = await orchestrator.process(
            "What Python tips do I have in my notes?"
        )
        assert response.answer
        assert len(response.agents_used) >= 2
        return (
            f"Agents: {response.agents_used}, "
            f"time: {response.processing_time_seconds}s"
        )

    await check("Research agent", check_research_agent)
    await check("Synthesis agent", check_synthesis_agent)
    await check("Orchestrator", check_orchestrator)

    # ── 6. Observability ──────────────────────────────────────────
    console.print("\n[bold]6. Observability[/bold]")

    async def check_logfire():
        import logfire
        logfire.configure(
            service_name="verify-step10",
            send_to_logfire=False
        )
        with logfire.span("final-verify"):
            logfire.info("verification", step=10)
        return "Logfire spans working"

    async def check_metrics():
        from src.observability.metrics import agent_metrics
        agent_metrics.record_call(1.0, "high")
        summary = agent_metrics.summary()
        assert summary["total_calls"] > 0
        return f"Metrics: {summary['total_calls']} calls tracked"

    await check("Logfire tracing", check_logfire)
    await check("Agent metrics", check_metrics)

    # ── 7. Evaluation System ──────────────────────────────────────
    console.print("\n[bold]7. Evaluation System[/bold]")

    async def check_scorer():
        from src.evaluation.scorer import score_response
        from src.evaluation.models import ExpectedOutput
        score = score_response(
            "Python list comprehensions are fast and concise",
            ExpectedOutput(
                must_contain=["python", "list"],
                min_length=20,
            ),
        )
        assert 0 <= score.total_score <= 1
        return f"Scorer works, sample score: {score.total_score:.3f}"

    async def check_eval_dataset():
        from src.evaluation.dataset import (
            RAG_EVAL_CASES, BASELINE_EVAL_CASES
        )
        assert len(RAG_EVAL_CASES) >= 3
        assert len(BASELINE_EVAL_CASES) >= 2
        return (
            f"RAG: {len(RAG_EVAL_CASES)} cases, "
            f"Baseline: {len(BASELINE_EVAL_CASES)} cases"
        )

    async def check_mini_eval():
        from src.evaluation.evaluator import (
            evaluate_system, run_baseline
        )
        from src.evaluation.dataset import BASELINE_EVAL_CASES
        summary = await evaluate_system(
            "Quick-Test",
            BASELINE_EVAL_CASES[:1],
            run_baseline,
        )
        assert summary.total_cases == 1
        return (
            f"Mini eval passed, "
            f"score: {summary.avg_score:.3f}"
        )

    await check("Scorer", check_scorer)
    await check("Eval dataset", check_eval_dataset)
    await check("Mini eval run", check_mini_eval)

    # ── 8. CLI System ─────────────────────────────────────────────
    console.print("\n[bold]8. CLI System[/bold]")

    async def check_cli_imports():
        from src.cli.display import console, print_success
        from src.cli.commands import handle_search, handle_memory
        from src.cli.app import SecondBrainCLI
        return "All CLI modules importable"

    async def check_cli_routing():
        from src.cli.app import SecondBrainCLI
        cli = SecondBrainCLI()
        result = await cli.route_command("/quit")
        assert result is False
        result = await cli.route_command("/help")
        assert result is True
        return "Command routing works"

    async def check_cli_search():
        from src.cli.commands import handle_search
        await handle_search("carbonara")
        return "Search command executed"

    await check("CLI imports", check_cli_imports)
    await check("CLI routing", check_cli_routing)
    await check("CLI search", check_cli_search)

    # ── Final Summary ─────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in results if ok)
    failed = sum(1 for _, ok, _ in results if not ok)
    total = len(results)

    console.print("\n" + "=" * 60)

    if all_good:
        console.print(Panel(
            f"[bold green]🎉 ALL {total} CHECKS PASSED![/bold green]\n\n"
            "Your Second Brain is complete and working!\n\n"
            "[bold]What you built:[/bold]\n"
            "  ✅ RAG system with ChromaDB\n"
            "  ✅ Persistent memory with TinyDB\n"
            "  ✅ PII guardrails with regex detection\n"
            "  ✅ Multi-agent orchestration\n"
            "  ✅ OTEL observability with Logfire\n"
            "  ✅ Evaluation-driven development\n"
            "  ✅ Rich CLI interface\n\n"
            "[bold]Next steps:[/bold]\n"
            "  → python main.py          (use your second brain)\n"
            "  → python run_evals.py     (full evaluation)\n"
            "  → python generate_evidence.py  (evidence report)",
            style="green",
            padding=(1, 4),
        ))
    else:
        console.print(Panel(
            f"[yellow]⚠️  {passed}/{total} checks passed, "
            f"{failed} failed[/yellow]\n\n"
            "Check the errors above and fix them.\n"
            "Run this script again after fixing.",
            style="yellow",
        ))

    return all_good


if __name__ == "__main__":
    asyncio.run(verify())