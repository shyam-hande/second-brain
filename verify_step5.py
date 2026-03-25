# verify_step5.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 5 VERIFICATION - MEMORY")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.memory.models import Memory, MemoryType, UserProfile
        print("  ✅ memory models imported")

        from src.memory.memory_store import memory_store, MemoryStore
        print("  ✅ memory_store imported")

        from src.memory.memory_agent import (
            extract_and_save_memories,
            build_memory_context,
        )
        print("  ✅ memory_agent imported")

        from src.memory.session import ChatSession
        print("  ✅ ChatSession imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Save and retrieve memories
    print("\n💾 Memory Save/Retrieve Check:")
    try:
        from src.memory.memory_store import memory_store
        from src.memory.models import MemoryType

        # Save test memories
        m1 = memory_store.save_memory(
            content="User prefers bullet points over paragraphs",
            memory_type=MemoryType.PREFERENCE,
            importance=4,
            tags=["preference", "format"],
        )
        m2 = memory_store.save_memory(
            content="User is building a second brain in Python",
            memory_type=MemoryType.FACT,
            importance=5,
            tags=["project"],
        )

        print(f"  ✅ Saved memory: {m1.id[:8]}...")
        print(f"  ✅ Saved memory: {m2.id[:8]}...")

        # Retrieve all
        all_mem = memory_store.get_all_memories()
        print(f"  ✅ Total memories in store: {len(all_mem)}")

        # Search memories
        results = memory_store.search_memories("python")
        print(f"  ✅ Search 'python' found: {len(results)} memories")

        # Get by type
        prefs = memory_store.get_memories_by_type(MemoryType.PREFERENCE)
        print(f"  ✅ Preference memories: {len(prefs)}")

    except Exception as e:
        print(f"  ❌ Memory store failed: {e}")
        all_good = False

    # Test 3: User profile
    print("\n👤 User Profile Check:")
    try:
        from src.memory.memory_store import memory_store
        from src.memory.models import UserProfile

        profile = UserProfile(
            name="Shyam",
            preferences=["concise answers", "bullet points"],
            known_facts=["building second brain", "uses Python"],
            interests=["AI", "cooking", "productivity"],
        )
        memory_store.save_user_profile(profile)

        loaded = memory_store.get_user_profile()
        assert loaded.name == "Shyam"
        print(f"  ✅ Profile saved and loaded: {loaded.name}")
        print(f"  ✅ Interests: {loaded.interests}")

    except Exception as e:
        print(f"  ❌ User profile failed: {e}")
        all_good = False

    # Test 4: Memory context building
    print("\n🧠 Memory Context Check:")
    try:
        from src.memory.memory_agent import build_memory_context
        context = build_memory_context()
        has_content = len(context) > 0
        print(f"  {'✅' if has_content else '⚠️ '} Context built: {len(context)} chars")
        if context:
            print(f"  ✅ Preview: {context[:100]}...")
    except Exception as e:
        print(f"  ❌ Context building failed: {e}")
        all_good = False

    # Test 5: Memory extraction from conversation
    print("\n🔍 Memory Extraction Check:")
    try:
        from src.memory.memory_agent import extract_and_save_memories
        from src.memory.memory_store import memory_store

        before = len(memory_store.get_all_memories())

        test_conversation = """
        User: Hi! My name is Shyam and I love Italian food especially pizza.
        Assistant: Nice to meet you Shyam! Italian food is delicious.
        User: I always prefer short answers please, no long paragraphs.
        Assistant: Understood! I will keep it brief.
        User: I am currently learning about vector databases for my AI project.
        Assistant: Great topic! Vector databases are essential for semantic search.
        """

        saved = await extract_and_save_memories(test_conversation)
        after = len(memory_store.get_all_memories())

        print(f"  ✅ Extracted {saved} memories from conversation")
        print(f"  ✅ Memory count: {before} → {after}")

    except Exception as e:
        print(f"  ❌ Memory extraction failed: {e}")
        all_good = False

    # Test 6: Memory stats
    print("\n📊 Memory Stats Check:")
    try:
        stats = memory_store.get_stats()
        print(f"  ✅ Total memories: {stats['total_memories']}")
        print(f"  ✅ Total conversations: {stats['total_conversations']}")
        print(f"  ✅ Memory types: {stats['memory_types']}")
        print(f"  ✅ Has profile: {stats['has_profile']}")
    except Exception as e:
        print(f"  ❌ Stats failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 5 Complete! Ready for Step 6 (PII Guardrails)")
    else:
        print("❌ Fix errors above before Step 6")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())