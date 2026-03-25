# src/agents/mcp_agent.py
"""
Agent that uses MCP tools instead of calling
RAG/Memory directly.

Key difference from orchestrator:
  Orchestrator → explicitly calls research/synthesis agents
  MCP Agent    → autonomously decides which tools to use
"""
import os
import asyncio
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic import BaseModel
from src.config import settings
import logfire

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class MCPAgentResponse(BaseModel):
    """Response from MCP-powered agent."""
    answer: str
    confidence: str
    tools_used: list[str] = []


async def mcp_chat(message: str) -> MCPAgentResponse:
    """
    Chat using an agent connected to our MCP server.

    The agent sees the tools and autonomously decides
    which ones to call - we don't direct it explicitly.
    """
    with logfire.span("mcp_chat", message=message):

        # Connect to our MCP server via stdio
        mcp_server = MCPServerStdio(
            command="python",
            args=["src/mcp_servers/knowledge_base_server.py"],
            env={
                **os.environ,
                "PYTHONPATH": ".",
            },
        )

        agent = Agent(
            model=f"anthropic:{settings.model_name}",
            mcp_servers=[mcp_server],
            system_prompt="""
            You are a helpful personal second brain assistant.

            You have access to tools via MCP. Use them wisely:

            1. search_knowledge_base  
               → Use for ANY question about personal notes, 
                 recipes, documents or specific facts
               
            2. get_all_sources       
               → Use when user asks what documents are available
               
            3. get_memory_context    
               → Use to personalize responses with user preferences
               
            4. save_memory           
               → Use when user shares something important to remember
               
            5. check_pii             
               → Use before storing any sensitive text

            Rules:
            - Always search before answering factual questions
            - Always get memory context for personal questions
            - Save important new facts the user shares
            - Be transparent about which tools you used
            """,
            output_type=MCPAgentResponse,
        )

        # Run agent with MCP servers active
        async with agent.run_mcp_servers():
            result = await agent.run(message)
            return result.output