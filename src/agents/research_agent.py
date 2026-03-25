# src/agents/research_agent.py
"""
Research Agent - searches the knowledge base and
returns relevant findings.
"""
from pydantic_ai import Agent
from pydantic import BaseModel
from src.config import settings
import logfire
import os

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class ResearchResult(BaseModel):
    """What the research agent returns."""
    findings: list[str]          # list of relevant facts found
    sources: list[str]           # which files were used
    search_query_used: str       # what was actually searched
    confidence: str              # high / medium / low
    has_relevant_info: bool      # did we find anything useful?


research_agent = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are a research specialist for a personal knowledge base.

    Your job is to:
    1. Analyze what information is being requested
    2. Review the context provided from the knowledge base
    3. Extract the most relevant facts and details
    4. Report findings clearly and concisely

    Rules:
    - Only report what is actually in the provided context
    - If context is empty or irrelevant, say so honestly
    - List findings as clear bullet points
    - Always cite which source each finding came from
    - Do not make up information
    """,
    output_type=ResearchResult,
)


async def research(query: str) -> ResearchResult:
    """
    Research a query against the knowledge base.
    Combines vector search with LLM analysis.
    """
    with logfire.span("research_agent", query=query):

        # Step 1: Search the vector store
        from src.rag.vector_store import vector_store
        search_results = vector_store.search(query, top_k=4)

        # Step 2: Build context from results
        sources = []
        context_parts = []

        for result in search_results:
            if result["relevance_score"] > 0.2:
                filename = result["metadata"].get("filename", "unknown")
                category = result["metadata"].get("category", "")
                score = result["relevance_score"]
                context_parts.append(
                    f"[Source: {filename} | Score: {score}]\n"
                    f"{result['content']}"
                )
                if filename not in sources:
                    sources.append(filename)

        context_text = "\n\n---\n\n".join(context_parts)

        # Step 3: Ask agent to analyze the context
        prompt = f"""
Research Query: {query}

Knowledge Base Context:
{context_text if context_text else "No relevant documents found."}

Please analyze this context and extract relevant findings.
"""

        result = await research_agent.run(prompt)
        response = result.output
        response.search_query_used = query
        response.sources = sources

        logfire.info(
            "research_completed",
            query=query,
            findings_count=len(response.findings),
            sources=sources,
        )

        return response