# src/evaluation/evaluator.py
"""
Runs evaluation cases against different systems and
compares their performance.
"""
import asyncio
import time
import logfire
from src.evaluation.models import (
    EvalResult, EvalSummary, QueryInput, ExpectedOutput
)
from src.evaluation.scorer import score_response


async def run_baseline(query: str) -> tuple[str, list[str], float]:
    """
    Run query against BASELINE system.
    Plain agent, no RAG, no memory, no multi-agent.
    """
    from src.agents.base_agent import chat_async

    start = time.time()
    response, _ = await chat_async(query, use_memory=False)
    latency = time.time() - start

    return response.answer, [], latency


async def run_rag_system(query: str) -> tuple[str, list[str], float]:
    """
    Run query against RAG system.
    Agent + vector search, no multi-agent.
    """
    from src.rag.rag_agent import rag_chat

    start = time.time()
    response, _ = await rag_chat(query)
    latency = time.time() - start

    return response.answer, response.sources, latency


async def run_multiagent_system(query: str) -> tuple[str, list[str], float]:
    """
    Run query against MULTI-AGENT system.
    Full orchestrator + research + synthesis + memory.
    """
    from src.agents.orchestrator_agent import orchestrator

    start = time.time()
    response = await orchestrator.process(query)
    latency = time.time() - start

    return response.answer, response.sources, latency


async def evaluate_system(
    system_name: str,
    cases: list[dict],
    runner_func,
) -> EvalSummary:
    """
    Run all evaluation cases against one system.

    Args:
        system_name: name of system being tested
        cases: list of test cases from dataset.py
        runner_func: async function to run the system
    """
    results = []
    print(f"\n{'='*50}")
    print(f"Evaluating: {system_name}")
    print(f"Cases: {len(cases)}")
    print(f"{'='*50}")

    with logfire.span(f"evaluate_{system_name}", cases=len(cases)):

        for case in cases:
            case_id = case["id"]
            query_input: QueryInput = case["input"]
            expected: ExpectedOutput = case["expected"]

            print(f"\n  📋 Case {case_id}: {query_input.query[:50]}...")

            try:
                # Run the system
                answer, sources, latency = await runner_func(
                    query_input.query
                )

                # Score the response
                score = score_response(
                    actual_answer=answer,
                    expected=expected,
                    sources_used=sources,
                )

                result = EvalResult(
                    case_id=case_id,
                    query=query_input.query,
                    actual_answer=answer,
                    expected=expected,
                    score=score,
                    system_used=system_name,
                    latency_seconds=round(latency, 2),
                    sources_used=sources,
                )

                results.append(result)

                status = "✅ PASS" if score.passed else "❌ FAIL"
                print(f"  {status} | Score: {score.total_score:.2f} "
                      f"| Time: {latency:.1f}s "
                      f"| Sources: {sources}")

            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                logfire.error(
                    "eval_case_failed",
                    case_id=case_id,
                    error=str(e),
                )
                continue

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

    # Build summary
    if not results:
        return EvalSummary(
            system_name=system_name,
            total_cases=0,
            passed_cases=0,
            avg_score=0.0,
            avg_latency=0.0,
        )

    passed = [r for r in results if r.score.passed]
    avg_score = sum(r.score.total_score for r in results) / len(results)
    avg_latency = sum(r.latency_seconds for r in results) / len(results)

    # Scores by category
    by_category = {}
    for result in results:
        cat = case["input"].category if "input" in case else "general"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(result.score.total_score)

    scores_by_cat = {
        cat: round(sum(scores) / len(scores), 3)
        for cat, scores in by_category.items()
    }

    summary = EvalSummary(
        system_name=system_name,
        total_cases=len(results),
        passed_cases=len(passed),
        avg_score=round(avg_score, 3),
        avg_latency=round(avg_latency, 2),
        scores_by_category=scores_by_cat,
        pass_rate=round(len(passed) / len(results), 3),
    )

    logfire.info(
        "evaluation_complete",
        system=system_name,
        avg_score=avg_score,
        pass_rate=summary.pass_rate,
    )

    return summary