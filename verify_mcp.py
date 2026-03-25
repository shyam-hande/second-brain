# verify_mcp.py
"""
Full verification of MCP setup.
Run: python verify_mcp.py
"""
import asyncio
import json


async def verify():
    print("=" * 50)
    print("MCP VERIFICATION")
    print("=" * 50)

    all_good = True

    # ── Test 1: MCP package installed ─────────────────────────────
    print("\n📦 Package Check:")
    # NEW - works
    try:
        import mcp
        # mcp doesn't expose __version__ directly
        # use importlib instead
        from importlib.metadata import version
        try:
            mcp_version = version("mcp")
        except Exception:
            mcp_version = "installed"
        print(f"  ✅ mcp installed: {mcp_version}")
    except ImportError:
        print('  ❌ mcp not installed - run: pip install "mcp[cli]"')
        all_good = False
        return

    # ── Test 2: Server file exists ─────────────────────────────────
    print("\n📄 Server File Check:")
    import os
    server_path = "src/mcp_servers/knowledge_base_server.py"
    agent_path = "src/agents/mcp_agent.py"

    for path in [server_path, agent_path]:
        exists = os.path.isfile(path)
        print(f"  {'✅' if exists else '❌'} {path}")
        if not exists:
            all_good = False

    # ── Test 3: Server imports work ────────────────────────────────
    print("\n🔌 Server Import Check:")
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp import types
        print("  ✅ mcp.server imported")
        print("  ✅ mcp.server.stdio imported")
        print("  ✅ mcp.types imported")
    except Exception as e:
        print(f"  ❌ MCP server imports failed: {e}")
        all_good = False

    # ── Test 4: Client imports work ────────────────────────────────
    print("\n🖥️  Client Import Check:")
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        print("  ✅ mcp.ClientSession imported")
        print("  ✅ mcp.client.stdio imported")
    except Exception as e:
        print(f"  ❌ MCP client imports failed: {e}")
        all_good = False

    # ── Test 5: Connect to server and list tools ───────────────────
    print("\n🛠️  Server Connection Check:")
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters

        params = StdioServerParameters(
            command="python",
            args=["src/mcp_servers/knowledge_base_server.py"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()

                print(f"  ✅ Server connected")
                print(f"  ✅ Tools available: {len(tools.tools)}")

                expected_tools = [
                    "search_knowledge_base",
                    "get_all_sources",
                    "get_memory_context",
                    "save_memory",
                    "check_pii",
                ]

                tool_names = [t.name for t in tools.tools]
                for expected in expected_tools:
                    found = expected in tool_names
                    print(
                        f"  {'✅' if found else '❌'} "
                        f"Tool: {expected}"
                    )
                    if not found:
                        all_good = False

    except Exception as e:
        print(f"  ❌ Server connection failed: {e}")
        all_good = False

    # ── Test 6: Call a tool ────────────────────────────────────────
    print("\n🔍 Tool Call Check:")
    try:
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters

        params = StdioServerParameters(
            command="python",
            args=["src/mcp_servers/knowledge_base_server.py"],
            env=None,
        )

        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test search tool
                result = await session.call_tool(
                    "search_knowledge_base",
                    {"query": "pasta recipe", "top_k": 2},
                )
                data = json.loads(result.content[0].text)
                print(f"  ✅ search_knowledge_base called")
                print(f"  ✅ Found: {data.get('found')}")
                print(f"  ✅ Results: {data.get('count', 0)}")

                # Test PII tool
                result = await session.call_tool(
                    "check_pii",
                    {"text": "email: test@example.com"},
                )
                data = json.loads(result.content[0].text)
                print(f"  ✅ check_pii called")
                print(f"  ✅ PII detected: {data.get('has_pii')}")
                print(f"  ✅ Redacted: {data.get('redacted_text')}")

    except Exception as e:
        print(f"  ❌ Tool call failed: {e}")
        all_good = False

    # ── Test 7: MCP agent end to end ──────────────────────────────
    print("\n🤖 MCP Agent End-to-End Check:")
    try:
        from src.agents.mcp_agent import mcp_chat, MCPAgentResponse

        response = await mcp_chat(
            "What documents do you have access to?"
        )

        assert isinstance(response, MCPAgentResponse)
        assert response.answer
        print(f"  ✅ MCP agent responded")
        print(f"  ✅ Answer: {response.answer[:60]}...")
        print(f"  ✅ Confidence: {response.confidence}")

    except Exception as e:
        print(f"  ❌ MCP agent failed: {e}")
        all_good = False

    # ── Summary ────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    if all_good:
        print("✅ MCP Setup Complete!")
        print("\nWhat you can do now:")
        print("  python test_mcp_server.py  → test server directly")
        print("  python test_mcp_agent.py   → test agent with tools")
        print("  python gradio_app.py       → use MCP tab in browser")
    else:
        print("❌ Fix errors above before using MCP")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())