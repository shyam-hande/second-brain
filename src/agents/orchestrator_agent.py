# src/agents/orchestrator.py
"""
Orchestrator Agent - the conductor of the multi-agent system.

Pattern used: Supervisor/Orchestrator pattern
- Receives user message
- Decides which agents to invoke
- Passes results between agents
- Returns final synthesized answer
"""
from pydantic_ai import Agent
from pydantic import BaseModel
from src.config import settings
import logfire
import os
import time

os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


# ── What the orchestrator decides ─────────────────────────────────────────────
class OrchestratorPlan(BaseModel):
    """The orchestrator's plan for handling a query."""
    needs_research: bool        # should we search knowledge base?
    needs_memory: bool          # should we load memory context?
    query_type: str             # "factual" / "personal" / "task" / "chat"
    refined_search_query: str   # optimized query for vector search
    reasoning: str              # why this plan was chosen


# ── Final response to user ─────────────────────────────────────────────────────
class FinalResponse(BaseModel):
    """Complete response from the multi-agent system."""
    answer: str
    key_points: list[str] = []
    sources: list[str] = []
    confidence: str
    used_knowledge_base: bool
    used_memory: bool
    agents_used: list[str]
    processing_time_seconds: float = 0.0
    follow_up_suggestions: list[str] = []


# ── Orchestrator agent ─────────────────────────────────────────────────────────
orchestrator_agent = Agent(
    model=f"anthropic:{settings.model_name}",
    system_prompt="""
    You are an intelligent orchestrator for a personal second brain system.

    Your job is to analyze incoming queries and create an efficient plan:

    1. NEEDS RESEARCH = True if:
       - Question is about specific notes, recipes, or documents
       - User asks "what do I have..." or "what did I write..."
       - Question involves specific facts from their knowledge base

    2. NEEDS MEMORY = True if:
       - Question is personal or conversational
       - Would benefit from knowing user preferences
       - User refers to past conversations

    3. QUERY TYPES:
       - "factual": Looking for specific info from knowledge base
       - "personal": About the user's preferences or history
       - "task": User wants help doing something
       - "chat": General conversation

    4. REFINED SEARCH QUERY:
       - Optimize the query for vector search
       - Extract key nouns and concepts
       - Remove filler words

    Always choose the most efficient path.
    Not every query needs all agents.
    """,
    output_type=OrchestratorPlan,
)


class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents to answer queries.

    This is the main entry point for the second brain system.
    """

    def __init__(self):
        self.call_count = 0
        self.total_time = 0.0

    async def process(
        self,
        query: str,
        conversation_history=None,
    ) -> FinalResponse:
        """
        Process a query through the multi-agent pipeline.

        Steps:
        1. Orchestrator creates a plan
        2. Research agent searches (if needed)
        3. Memory agent loads context (if needed)
        4. Synthesis agent combines everything
        5. Return final answer
        """
        start_time = time.time()
        self.call_count += 1
        agents_used = ["orchestrator"]

        with logfire.span(
            "multi_agent_pipeline",
            query=query,
            call_number=self.call_count,
        ):
            # ── Step 1: Orchestrator plans ─────────────────────────
            logfire.info("orchestrator_planning", query=query)
            print(f"\n🎯 Orchestrator planning for: '{query[:50]}...'")

            plan_result = await orchestrator_agent.run(
                f"Plan how to answer this query: {query}"
            )
            plan = plan_result.output

            print(f"   Query type: {plan.query_type}")
            print(f"   Needs research: {plan.needs_research}")
            print(f"   Needs memory: {plan.needs_memory}")
            print(f"   Search query: '{plan.refined_search_query}'")
            print(f"   Reasoning: {plan.reasoning[:80]}...")

            logfire.info(
                "orchestrator_plan",
                query_type=plan.query_type,
                needs_research=plan.needs_research,
                needs_memory=plan.needs_memory,
            )

            # ── Step 2: Research Agent (if needed) ─────────────────
            research_findings = []
            research_sources = []
            has_kb_info = False

            if plan.needs_research:
                print("\n🔍 Research Agent searching...")
                agents_used.append("research")

                from src.agents.research_agent import research
                research_result = await research(plan.refined_search_query)

                research_findings = research_result.findings
                research_sources = research_result.sources
                has_kb_info = research_result.has_relevant_info

                print(f"   Found {len(research_findings)} findings")
                print(f"   Sources: {research_sources}")

                logfire.info(
                    "research_done",
                    findings=len(research_findings),
                    sources=research_sources,
                )

            # ── Step 3: Memory Context (if needed) ─────────────────
            memory_context = ""

            if plan.needs_memory:
                print("\n💾 Loading memory context...")
                agents_used.append("memory")

                from src.memory.memory_agent import build_memory_context
                memory_context = build_memory_context()

                print(f"   Memory context: {len(memory_context)} chars")
                logfire.info(
                    "memory_loaded",
                    context_length=len(memory_context),
                )

            # ── Step 4: Synthesis Agent combines everything ─────────
            print("\n🧠 Synthesis Agent combining results...")
            agents_used.append("synthesis")

            from src.agents.synthesis_agent import synthesize
            synthesis_result = await synthesize(
                original_query=query,
                research_findings=research_findings,
                research_sources=research_sources,
                memory_context=memory_context,
                has_knowledge_base_info=has_kb_info,
            )

            # ── Step 5: Build final response ───────────────────────
            duration = time.time() - start_time
            self.total_time += duration

            final = FinalResponse(
                answer=synthesis_result.final_answer,
                key_points=synthesis_result.key_points,
                sources=research_sources,
                confidence=synthesis_result.confidence,
                used_knowledge_base=synthesis_result.used_knowledge_base,
                used_memory=synthesis_result.used_memory,
                agents_used=agents_used,
                processing_time_seconds=round(duration, 2),
                follow_up_suggestions=synthesis_result.follow_up_suggestions,
            )

            logfire.info(
                "pipeline_completed",
                agents_used=agents_used,
                duration=duration,
                confidence=final.confidence,
            )

            print(f"\n✅ Pipeline complete in {duration:.2f}s")
            print(f"   Agents used: {agents_used}")

            return final

    def get_stats(self) -> dict:
        """Get orchestrator statistics."""
        return {
            "total_queries": self.call_count,
            "total_time_seconds": round(self.total_time, 2),
            "avg_time_seconds": round(
                self.total_time / self.call_count, 2
            ) if self.call_count > 0 else 0,
        }


# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()