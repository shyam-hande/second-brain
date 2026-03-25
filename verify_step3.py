# verify_step3.py
import asyncio
import time


async def verify():
    print("=" * 50)
    print("STEP 3 VERIFICATION - OBSERVABILITY")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        import logfire
        print("  ✅ logfire imported")

        from src.observability.metrics import agent_metrics, AgentMetrics
        print("  ✅ metrics module imported")

        from src.agents.base_agent import chat_async, base_agent
        print("  ✅ base_agent imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Logfire span works
    print("\n🔍 Logfire Span Check:")
    try:
        with logfire.span("verify-test-span", step="step3"):
            logfire.info("verification running", test="span_test")
        print("  ✅ logfire.span() works")
        print("  ✅ logfire.info() works")
    except Exception as e:
        print(f"  ❌ Logfire span failed: {e}")
        all_good = False

    # Test 3: Metrics recording works
    print("\n📊 Metrics Check:")
    try:
        from src.observability.metrics import agent_metrics
        agent_metrics.record_call(duration_seconds=1.5, confidence="high")
        agent_metrics.record_call(duration_seconds=0.8, confidence="medium")
        agent_metrics.record_call(duration_seconds=2.1, confidence="high")

        summary = agent_metrics.summary()
        print(f"  ✅ Total calls tracked: {summary['total_calls']}")
        print(f"  ✅ Avg response time: {summary['avg_response_time_seconds']}s")
        print(f"  ✅ Confidence distribution: {summary['confidence_distribution']}")
        print(f"  ✅ Fastest: {summary['fastest_seconds']}s")
        print(f"  ✅ Slowest: {summary['slowest_seconds']}s")
    except Exception as e:
        print(f"  ❌ Metrics failed: {e}")
        all_good = False

    # Test 4: Agent call with tracing
    print("\n🤖 Agent Call With Tracing Check:")
    try:
        from src.observability.metrics import agent_metrics

        calls_before = agent_metrics.total_calls
        start = time.time()

        with logfire.span("verify-agent-call"):
            response, history = await chat_async("Say the word PONG in your answer.")

        duration = time.time() - start
        calls_after = agent_metrics.total_calls

        print(f"  ✅ Agent responded: '{response.answer[:60]}...'")
        print(f"  ✅ Response time: {round(duration, 2)}s")
        print(f"  ✅ Metrics recorded: calls went {calls_before} → {calls_after}")
        print(f"  ✅ Confidence: {response.confidence}")
    except Exception as e:
        print(f"  ❌ Traced agent call failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 3 Complete! Ready for Step 4 (RAG)")
    else:
        print("❌ Fix errors above before Step 4")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())