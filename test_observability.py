# test_observability.py
import asyncio
import logfire
from src.agents.base_agent import base_agent, chat_async, AgentResponse


async def test_with_tracing():
    print("=" * 60)
    print("OBSERVABILITY TEST - Watch the traces below!")
    print("=" * 60)

    # ── Test 1: Simple span ────────────────────────────────────────
    print("\n📍 Test 1: Manual span")
    with logfire.span("test-manual-span", test_name="observability"):
        print("  This operation is being traced!")
        result = await base_agent.run("What is observability in software?")
        print(f"  Answer: {result.output.answer[:100]}...")

    # ── Test 2: Nested spans ───────────────────────────────────────
    print("\n📍 Test 2: Nested spans (parent → child)")
    with logfire.span("parent-operation"):
        with logfire.span("child-operation-1"):
            r1 = await base_agent.run("Name one benefit of tracing.")
            print(f"  Child 1 answer: {r1.output.answer[:80]}...")

        with logfire.span("child-operation-2"):
            r2 = await base_agent.run(
                "Name one benefit of logging.",
                message_history=r1.new_messages()
            )
            print(f"  Child 2 answer: {r2.output.answer[:80]}...")

    # ── Test 3: Log structured data ────────────────────────────────
    print("\n📍 Test 3: Structured logging")
    with logfire.span("structured-log-test"):
        response, history = await chat_async("What is 10 * 10?")

        # Log structured data alongside the trace
        logfire.info(
            "Chat completed",
            answer=response.answer,
            confidence=response.confidence,
            message_count=len(history),
        )
        print(f"  Answer: {response.answer}")
        print(f"  Confidence: {response.confidence}")
        print(f"  Messages in history: {len(history)}")

    print("\n" + "=" * 60)
    print("✅ All traces captured!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_with_tracing())