# test_agent_basic.py
import asyncio
from src.agents.base_agent import base_agent, AgentResponse


async def test_basic_chat():
    print("=" * 50)
    print("TEST 1: Basic Question")
    print("=" * 50)
    
    result = await base_agent.run(
        "What is a second brain and why is it useful?"
    )
    
    # result.output is your AgentResponse object (was result.data before)
    response: AgentResponse = result.output
    
    print(f"Answer: {response.answer}")
    print(f"Confidence: {response.confidence}")
    print(f"Sources: {response.sources_used}")


async def test_followup():
    print("\n" + "=" * 50)
    print("TEST 2: Message History (Context)")
    print("=" * 50)
    
    # First message
    result1 = await base_agent.run(
        "My name is Alex and I love cooking Italian food."
    )
    print(f"Response 1: {result1.output.answer}")
    
    # Second message - passing history from first
    result2 = await base_agent.run(
        "What kind of food did I say I love?",
        message_history=result1.new_messages(),
    )
    print(f"Response 2 (should mention Italian): {result2.output.answer}")


async def main():
    print("\n🧠 Testing Second Brain Base Agent\n")
    await test_basic_chat()
    await test_followup()
    print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(main())