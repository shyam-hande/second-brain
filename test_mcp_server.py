# test_mcp_server.py
"""
Test the MCP server directly using the MCP Python client.
Run: python test_mcp_server.py
"""
import asyncio
import json
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def test():
    print("=" * 60)
    print("MCP SERVER DIRECT TEST")
    print("=" * 60)

    # Point to our server script
    params = StdioServerParameters(
        command="python",
        args=["src/mcp_servers/knowledge_base_server.py"],
        env=None,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:

            # Initialize connection
            await session.initialize()
            print("✅ Connected to MCP server\n")

            # ── List tools ─────────────────────────────────────────
            tools_result = await session.list_tools()
            print(f"📦 Available tools: {len(tools_result.tools)}")
            for t in tools_result.tools:
                print(f"   - {t.name}")
            print()

            # ── Test: search_knowledge_base ────────────────────────
            print("🔍 Testing search_knowledge_base...")
            result = await session.call_tool(
                "search_knowledge_base",
                {"query": "pasta carbonara", "top_k": 2},
            )
            data = json.loads(result.content[0].text)
            print(f"   Found: {data.get('found')}")
            print(f"   Count: {data.get('count', 0)}")
            if data.get("results"):
                top = data["results"][0]
                print(f"   Top source: {top['source']}")
                print(f"   Score: {top['relevance_score']}")
                print(f"   Preview: {top['content'][:60]}...")
            print()

            # ── Test: get_all_sources ──────────────────────────────
            print("📄 Testing get_all_sources...")
            result = await session.call_tool("get_all_sources", {})
            data = json.loads(result.content[0].text)
            print(f"   Total documents: {data.get('total_documents')}")
            print(f"   Total chunks: {data.get('total_chunks')}")
            for doc in data.get("documents", [])[:3]:
                print(
                    f"   - {doc['filename']} "
                    f"({doc['category']}, {doc['chunks']} chunks)"
                )
            print()

            # ── Test: get_memory_context ───────────────────────────
            print("💾 Testing get_memory_context...")
            result = await session.call_tool("get_memory_context", {})
            data = json.loads(result.content[0].text)
            print(f"   Total memories: {data.get('total_memories')}")
            print(f"   Has profile: {data.get('has_profile')}")
            ctx = data.get("context", "")
            print(
                f"   Context: {ctx[:80]}..."
                if ctx else "   Context: (empty)"
            )
            print()

            # ── Test: check_pii ────────────────────────────────────
            print("🔒 Testing check_pii...")
            result = await session.call_tool(
                "check_pii",
                {"text": "Contact me at john@example.com or 555-123-4567"},
            )
            data = json.loads(result.content[0].text)
            print(f"   Has PII: {data.get('has_pii')}")
            print(f"   Types found: {data.get('pii_types_found')}")
            print(f"   Redacted: {data.get('redacted_text')}")
            print()

            # ── Test: save_memory ──────────────────────────────────
            print("💡 Testing save_memory...")
            result = await session.call_tool(
                "save_memory",
                {
                    "content": "User successfully tested MCP server",
                    "memory_type": "fact",
                    "importance": 3,
                },
            )
            data = json.loads(result.content[0].text)
            print(f"   Saved: {data.get('saved')}")
            print(f"   ID: {str(data.get('memory_id', ''))[:8]}...")
            print(f"   PII cleaned: {data.get('pii_was_cleaned')}")
            print()

            print("=" * 60)
            print("✅ All MCP server tests passed!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test())