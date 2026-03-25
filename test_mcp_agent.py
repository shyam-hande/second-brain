# test_mcp_agent.py
"""
Test the full MCP agent end to end.
Run: python test_mcp_agent.py
"""
import asyncio
from src.agents.mcp_agent import mcp_chat


async def main():
    print("=" * 60)
    print("MCP AGENT TEST")
    print("=" * 60)

    questions = [
        "What pasta recipes do I have?",
        "What Python tips are in my notes?",
        "What documents do you have access to?",
        "Remember this: I prefer dark mode in all my tools",
    ]

    for question in questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)

        response = await mcp_chat(question)

        print(f"💬 Answer: {response.answer}")
        print(f"🎯 Confidence: {response.confidence}")
        if response.tools_used:
            print(f"🔌 Tools used: {response.tools_used}")
        print()

    print("=" * 60)
    print("✅ MCP Agent tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())