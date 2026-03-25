# src/rag/rag_agent.py
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from src.config import settings
from src.rag.vector_store import vector_store
import logfire
import os

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class RAGResponse(BaseModel):
    """Structured response from RAG agent."""
    answer: str
    confidence: str
    sources: list[str] = []      # which files were used
    used_knowledge_base: bool = False  # did it use RAG or not?


# ── Create RAG agent ───────────────────────────────────────────────────────────
rag_agent = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are a helpful personal second brain assistant.

    You have access to the user's personal knowledge base containing
    their notes, recipes, and other documents.

    When answering:
    1. First check if relevant context was provided from the knowledge base
    2. If yes, use it to give a specific, accurate answer
    3. If no context provided, answer from general knowledge and say so
    4. Always cite which document/source you used if applicable
    5. Be concise but complete

    The context from the knowledge base will be provided in the user message
    in a section marked [KNOWLEDGE BASE CONTEXT].
    """,
    output_type=RAGResponse,
)


async def rag_chat(message: str, history=None) -> tuple[RAGResponse, list]:
    """
    Chat with RAG - searches knowledge base before answering.
    
    Flow:
    1. Search vector store for relevant docs
    2. Inject found docs into the prompt
    3. Agent answers using both docs + its own knowledge
    """
    with logfire.span("rag_chat", message=message):

        # Step 1: Search the knowledge base
        search_results = vector_store.search(query=message)

        # Step 2: Build context string from results
        context_text = ""
        sources = []

        if search_results:
            context_parts = []
            for r in search_results:
                filename = r["metadata"].get("filename", "unknown")
                category = r["metadata"].get("category", "")
                score = r["relevance_score"]

                # Only use results with decent relevance
                if score > 0.3:
                    context_parts.append(
                        f"[Source: {filename} | Relevance: {score}]\n{r['content']}"
                    )
                    if filename not in sources:
                        sources.append(filename)

            if context_parts:
                context_text = "\n\n---\n\n".join(context_parts)

        # Step 3: Build the full prompt
        if context_text:
            full_message = f"""
{message}

[KNOWLEDGE BASE CONTEXT]
{context_text}
[END CONTEXT]
"""
            logfire.info("rag_context_found", sources=sources)
        else:
            full_message = message
            logfire.info("rag_no_context_found", query=message)

        # Step 4: Run the agent
        result = await rag_agent.run(
            full_message,
            message_history=history or [],
        )

        # Step 5: Enrich the response with source info
        response = result.output
        response.sources = sources
        response.used_knowledge_base = bool(sources)

        return response, result.new_messages()