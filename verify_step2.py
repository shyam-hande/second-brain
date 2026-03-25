# verify_step2.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 2 VERIFICATION")
    print("=" * 50)
    
    all_good = True
    
    # Test 1: Can we import the agent?
    print("\n📦 Import Check:")
    try:
        from src.agents.base_agent import base_agent, AgentResponse, chat, chat_async
        print("  ✅ base_agent imported")
        print("  ✅ AgentResponse imported")
        print("  ✅ chat imported")
        print("  ✅ chat_async imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return
    
    # Test 2: Does the agent return correct type?
    print("\n🤖 Agent Response Type Check:")
    try:
        result = await base_agent.run("Say the word: HELLO")
        assert isinstance(result.output, AgentResponse), "Wrong return type!"
        print(f"  ✅ Returns AgentResponse")
        print(f"  ✅ Has answer field: '{result.output.answer[:50]}...'")
        print(f"  ✅ Has confidence field: '{result.output.confidence}'")
        print(f"  ✅ Has sources_used field: {result.output.sources_used}")
    except Exception as e:
        print(f"  ❌ Agent run failed: {e}")
        all_good = False
    
    # Test 3: Does message history work?
    print("\n💬 Message History Check:")
    try:
        result1 = await base_agent.run("Remember the number 42.")
        result2 = await base_agent.run(
            "What number did I just ask you to remember?",
            message_history=result1.new_messages()
        )
        answer = result2.output.answer
        has_42 = "42" in answer
        print(f"  {'✅' if has_42 else '❌'} History preserved: {answer[:80]}")
        if not has_42:
            all_good = False
    except Exception as e:
        print(f"  ❌ History test failed: {e}")
        all_good = False
    
    # Test 4: Async wrapper works?
    print("\n🔄 Async Wrapper Check:")
    try:
        # Inside async context, use chat_async directly
        response, new_history = await chat_async("What is 2+2?")
        assert isinstance(response, AgentResponse)
        assert new_history is not None
        print(f"  ✅ chat_async() works")
        print(f"  ✅ Answer: {response.answer}")
        print(f"  ✅ Returns tuple (response, history)")
    except Exception as e:
        print(f"  ❌ Async wrapper failed: {e}")
        all_good = False

    # Test 5: Check model name is correct
    print("\n🔧 Model Config Check:")
    try:
        from src.config import settings
        print(f"  ✅ Model in config: {settings.model_name}")
        print(f"  ✅ API key set: {'yes' if settings.anthropic_api_key else 'no'}")
    except Exception as e:
        print(f"  ❌ Config check failed: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 2 Complete! Ready for Step 3 (OTEL Observability)")
    else:
        print("❌ Fix errors above before Step 3")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())