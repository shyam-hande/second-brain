# verify_step9.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 9 VERIFICATION - CLI")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.cli.display import (
            console, print_welcome, print_help,
            print_answer, print_memories,
            print_stats, print_error,
        )
        print("  ✅ display module imported")

        from src.cli.commands import (
            handle_chat, handle_search, handle_memory,
            handle_remember, handle_stats, handle_eval,
        )
        print("  ✅ commands module imported")

        from src.cli.app import SecondBrainCLI
        print("  ✅ CLI app imported")

    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Display functions work
    print("\n🖥️  Display Functions Check:")
    try:
        from src.cli.display import (
            print_success, print_error,
            print_info, print_warning,
        )
        print_success("Test success message")
        print_info("Test info message")
        print_warning("Test warning message")
        print("  ✅ All display functions work")
    except Exception as e:
        print(f"  ❌ Display failed: {e}")
        all_good = False

    # Test 3: Command routing
    print("\n🔀 Command Routing Check:")
    try:
        from src.cli.app import SecondBrainCLI
        cli = SecondBrainCLI()

        # Test quit command returns False
        result = await cli.route_command("/quit")
        assert result is False, "Quit should return False"
        print("  ✅ /quit returns False")

        # Test help command returns True
        result = await cli.route_command("/help")
        assert result is True, "Help should return True"
        print("  ✅ /help returns True")

        # Test unknown command
        result = await cli.route_command("/unknown_command")
        assert result is True, "Unknown should return True (not crash)"
        print("  ✅ Unknown command handled gracefully")

        # Test empty input
        result = await cli.route_command("")
        assert result is True, "Empty input should return True"
        print("  ✅ Empty input handled")

    except Exception as e:
        print(f"  ❌ Command routing failed: {e}")
        all_good = False

    # Test 4: Search command
    print("\n🔍 Search Command Check:")
    try:
        from src.cli.commands import handle_search
        await handle_search("pasta carbonara")
        print("  ✅ /search command works")
    except Exception as e:
        print(f"  ❌ Search command failed: {e}")
        all_good = False

    # Test 5: Memory command
    print("\n💾 Memory Command Check:")
    try:
        from src.cli.commands import handle_memory, handle_remember
        await handle_remember("User is testing the second brain system")
        await handle_memory()
        print("  ✅ /remember command works")
        print("  ✅ /memory command works")
    except Exception as e:
        print(f"  ❌ Memory command failed: {e}")
        all_good = False

    # Test 6: Stats command
    print("\n📊 Stats Command Check:")
    try:
        from src.cli.commands import handle_stats
        await handle_stats()
        print("  ✅ /stats command works")
    except Exception as e:
        print(f"  ❌ Stats command failed: {e}")
        all_good = False

    # Test 7: Chat command (single message)
    print("\n🤖 Chat Command Check:")
    try:
        from src.cli.commands import handle_chat
        from src.cli.app import SecondBrainCLI
        cli = SecondBrainCLI()
        await handle_chat("What is a second brain?", cli)
        print("  ✅ /chat command works")
    except Exception as e:
        print(f"  ❌ Chat command failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 9 Complete! Ready for Step 10 (Final Polish)")
    else:
        print("❌ Fix errors above before Step 10")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())