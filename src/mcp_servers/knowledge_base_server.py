# src/mcp_servers/knowledge_base_server.py
"""
MCP Server that exposes Second Brain as tools.

Tools provided:
  - search_knowledge_base  → semantic search your notes
  - get_all_sources        → list all documents
  - get_memory_context     → get user memory/preferences
  - save_memory            → persist a new memory
  - check_pii              → detect and redact PII
"""
import asyncio
import json
import sys
import os

# Make sure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Create the server instance
server = Server("second-brain-kb")


# ── List available tools ───────────────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """Tell MCP clients what tools this server provides."""
    return [
        types.Tool(
            name="search_knowledge_base",
            description=(
                "Search the personal knowledge base using semantic search. "
                "Returns relevant chunks from notes, recipes and documents. "
                "Use when user asks about their personal notes or documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default 3)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="get_all_sources",
            description=(
                "List all documents stored in the knowledge base. "
                "Use to show the user what files are available."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_memory_context",
            description=(
                "Get the user's personal memory context including "
                "preferences, known facts and recent conversations. "
                "Use this to personalize responses."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="save_memory",
            description=(
                "Save an important fact or preference to persistent memory. "
                "Use when the user shares something important about themselves."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The fact or preference to remember",
                    },
                    "memory_type": {
                        "type": "string",
                        "enum": ["preference", "fact", "context"],
                        "description": "Type of memory",
                        "default": "fact",
                    },
                    "importance": {
                        "type": "integer",
                        "description": "Importance 1-5 (5 = most important)",
                        "default": 3,
                    },
                },
                "required": ["content"],
            },
        ),
        types.Tool(
            name="check_pii",
            description=(
                "Check if text contains PII and return redacted version. "
                "Always use before storing any user-provided text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to check for PII",
                    },
                },
                "required": ["text"],
            },
        ),
    ]


# ── Handle tool calls ──────────────────────────────────────────────────────────
@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict,
) -> list[types.TextContent]:
    """Route tool calls to the correct handler."""

    # ── search_knowledge_base ──────────────────────────────────────
    if name == "search_knowledge_base":
        try:
            from src.rag.vector_store import vector_store

            query = arguments["query"]
            top_k = arguments.get("top_k", 3)
            results = vector_store.search(query, top_k=top_k)

            if not results:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "found": False,
                        "message": "No relevant documents found",
                        "results": [],
                    })
                )]

            formatted = []
            for r in results:
                formatted.append({
                    "content": r["content"],
                    "source": r["metadata"].get("filename", "unknown"),
                    "category": r["metadata"].get("category", ""),
                    "relevance_score": r["relevance_score"],
                })

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "found": True,
                    "count": len(formatted),
                    "results": formatted,
                }, indent=2)
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    # ── get_all_sources ────────────────────────────────────────────
    elif name == "get_all_sources":
        try:
            from src.rag.vector_store import vector_store

            all_data = vector_store.collection.get()
            sources = {}

            for metadata in all_data.get("metadatas", []):
                filename = metadata.get("filename", "unknown")
                category = metadata.get("category", "general")
                if filename not in sources:
                    sources[filename] = {
                        "filename": filename,
                        "category": category,
                        "chunks": 0,
                    }
                sources[filename]["chunks"] += 1

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "total_documents": len(sources),
                    "total_chunks": len(all_data.get("ids", [])),
                    "documents": list(sources.values()),
                }, indent=2)
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    # ── get_memory_context ─────────────────────────────────────────
    elif name == "get_memory_context":
        try:
            from src.memory.memory_agent import build_memory_context
            from src.memory.memory_store import memory_store

            context = build_memory_context()
            stats = memory_store.get_stats()

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "context": context,
                    "total_memories": stats["total_memories"],
                    "has_profile": stats["has_profile"],
                }, indent=2)
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    # ── save_memory ────────────────────────────────────────────────
    elif name == "save_memory":
        try:
            from src.memory.memory_store import memory_store
            from src.memory.models import MemoryType
            from src.guardrails.guardrail import pii_guardrail

            content = arguments["content"]
            memory_type_str = arguments.get("memory_type", "fact")
            importance = arguments.get("importance", 3)

            # Always clean PII before saving
            clean_content = pii_guardrail.process_for_storage(content)
            was_cleaned = clean_content != content

            type_map = {
                "preference": MemoryType.PREFERENCE,
                "fact": MemoryType.FACT,
                "context": MemoryType.CONTEXT,
            }
            mem_type = type_map.get(memory_type_str, MemoryType.FACT)

            memory = memory_store.save_memory(
                content=clean_content,
                memory_type=mem_type,
                importance=importance,
                tags=["mcp", "auto-saved"],
            )

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "saved": True,
                    "memory_id": memory.id,
                    "content": clean_content,
                    "pii_was_cleaned": was_cleaned,
                    "type": memory_type_str,
                    "importance": importance,
                }, indent=2)
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    # ── check_pii ──────────────────────────────────────────────────
    elif name == "check_pii":
        try:
            from src.guardrails.pii_detector import (
                redact_pii, get_pii_report
            )

            text = arguments["text"]
            redacted, matches = redact_pii(text)
            report = get_pii_report(text)

            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "original_text": text,
                    "redacted_text": redacted,
                    "has_pii": report["has_pii"],
                    "pii_types_found": report["types_found"],
                    "total_items": report["total_found"],
                }, indent=2)
            )]

        except Exception as e:
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]

    else:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"})
        )]


# ── Run server ─────────────────────────────────────────────────────────────────
async def main():
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())