# verify_step7.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 7 VERIFICATION - MULTI-AGENT")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.agents.research_agent import research_agent, research
        print("  ✅ research_agent imported")

        from src.agents.synthesis_agent import synthesis_agent, synthesize
        print("  ✅ synthesis_agent imported")

        from src.agents.orchestrator_agent import (
            orchestrator_agent,
            MultiAgentOrchestrator,
            orchestrator,
            FinalResponse,
        )
        print("  ✅ orchestrator imported")
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Research agent works
    print("\n🔍 Research Agent Check:")
    try:
        from src.agents.research_agent import research
        result = await research("pasta carbonara recipe")

        print(f"  ✅ Research completed")
        print(f"  ✅ Findings: {len(result.findings)}")
        print(f"  ✅ Sources: {result.sources}")
        print(f"  ✅ Has info: {result.has_relevant_info}")
        print(f"  ✅ Confidence: {result.confidence}")

        if result.findings:
            print(f"  ✅ Sample finding: {result.findings[0][:60]}...")
    except Exception as e:
        print(f"  ❌ Research agent failed: {e}")
        all_good = False

    # Test 3: Synthesis agent works
    print("\n🧠 Synthesis Agent Check:")
    try:
        from src.agents.synthesis_agent import synthesize
        result = await synthesize(
            original_query="How do I make pasta?",
            research_findings=[
                "Cook pasta until al dente",
                "Use guanciale for carbonara",
                "Never add cream to carbonara",
            ],
            research_sources=["pasta_carbonara.md"],
            memory_context="User enjoys Italian cooking",
            has_knowledge_base_info=True,
        )

        print(f"  ✅ Synthesis completed")
        print(f"  ✅ Answer length: {len(result.final_answer)} chars")
        print(f"  ✅ Key points: {len(result.key_points)}")
        print(f"  ✅ Used KB: {result.used_knowledge_base}")
        print(f"  ✅ Used memory: {result.used_memory}")
        print(f"  ✅ Confidence: {result.confidence}")
    except Exception as e:
        print(f"  ❌ Synthesis agent failed: {e}")
        all_good = False

    # Test 4: Orchestrator planning
    print("\n🎯 Orchestrator Planning Check:")
    try:
        from src.agents.orchestrator_agent import orchestrator_agent, OrchestratorPlan

        plan_result = await orchestrator_agent.run(
            "Plan how to answer this query: What pasta recipes do I have?"
        )
        plan = plan_result.output

        print(f"  ✅ Plan created")
        print(f"  ✅ Query type: {plan.query_type}")
        print(f"  ✅ Needs research: {plan.needs_research}")
        print(f"  ✅ Needs memory: {plan.needs_memory}")
        print(f"  ✅ Search query: {plan.refined_search_query}")

        # A question about recipes should trigger research
        if not plan.needs_research:
            print("  ⚠️  Expected needs_research=True for recipe query")
    except Exception as e:
        print(f"  ❌ Orchestrator planning failed: {e}")
        all_good = False

    # Test 5: Full pipeline
    print("\n🔄 Full Pipeline Check:")
    try:
        from src.agents.orchestrator_agent import orchestrator, FinalResponse

        response = await orchestrator.process(
            "What carbonara ingredients do I have in my recipes?"
        )

        assert isinstance(response, FinalResponse)
        print(f"  ✅ Pipeline completed")
        print(f"  ✅ Answer: {response.answer[:80]}...")
        print(f"  ✅ Agents used: {response.agents_used}")
        print(f"  ✅ Sources: {response.sources}")
        print(f"  ✅ Time: {response.processing_time_seconds}s")
        print(f"  ✅ Confidence: {response.confidence}")

        # Should have used at least 2 agents
        if len(response.agents_used) < 2:
            print("  ⚠️  Expected multiple agents to be used")

    except Exception as e:
        print(f"  ❌ Full pipeline failed: {e}")
        all_good = False

    # Test 6: Orchestrator stats
    print("\n📊 Stats Check:")
    try:
        from src.agents.orchestrator_agent import orchestrator
        stats = orchestrator.get_stats()
        print(f"  ✅ Total queries: {stats['total_queries']}")
        print(f"  ✅ Total time: {stats['total_time_seconds']}s")
        print(f"  ✅ Avg time: {stats['avg_time_seconds']}s")
    except Exception as e:
        print(f"  ❌ Stats failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 7 Complete! Ready for Step 8 (Pydantic Evals)")
    else:
        print("❌ Fix errors above before Step 8")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())