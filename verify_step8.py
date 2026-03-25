# verify_step8.py
import asyncio


async def verify():
    print("=" * 50)
    print("STEP 8 VERIFICATION - PYDANTIC EVALS")
    print("=" * 50)

    all_good = True

    # Test 1: Imports
    print("\n📦 Import Check:")
    try:
        from src.evaluation.models import (
            QueryInput, ExpectedOutput, EvalScore,
            EvalResult, EvalSummary
        )
        print("  ✅ evaluation models imported")

        from src.evaluation.scorer import score_response
        print("  ✅ scorer imported")

        from src.evaluation.dataset import (
            RAG_EVAL_CASES, BASELINE_EVAL_CASES,
            MULTIAGENT_EVAL_CASES
        )
        print("  ✅ dataset imported")

        from src.evaluation.evaluator import (
            evaluate_system, run_baseline,
            run_rag_system, run_multiagent_system
        )
        print("  ✅ evaluator imported")

    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        all_good = False
        return

    # Test 2: Scorer works correctly
    print("\n🎯 Scorer Check:")
    try:
        from src.evaluation.scorer import score_response
        from src.evaluation.models import ExpectedOutput

        # Perfect answer
        perfect = score_response(
            actual_answer="The pasta carbonara recipe uses eggs, "
                          "guanciale, pecorino cheese and black pepper. "
                          "Never add cream to authentic carbonara.",
            expected=ExpectedOutput(
                must_contain=["eggs", "carbonara"],
                should_contain=["guanciale", "pecorino"],
                must_not_contain=[],
                min_length=30,
                should_use_sources=False,
            ),
        )
        print(f"  ✅ Perfect answer score: {perfect.total_score:.3f}")
        print(f"  ✅ Passed: {perfect.passed}")

        # Bad answer - missing required content
        bad = score_response(
            actual_answer="I don't know",
            expected=ExpectedOutput(
                must_contain=["eggs", "carbonara"],
                should_contain=["guanciale"],
                min_length=50,
                should_use_sources=True,
            ),
        )
        print(f"  ✅ Bad answer score: {bad.total_score:.3f}")
        print(f"  ✅ Passed: {bad.passed}")

        # Verify perfect > bad
        assert perfect.total_score > bad.total_score
        print(f"  ✅ Perfect ({perfect.total_score:.3f}) "
              f"> Bad ({bad.total_score:.3f}) ✓")

    except Exception as e:
        print(f"  ❌ Scorer failed: {e}")
        all_good = False

    # Test 3: Dataset is well formed
    print("\n📋 Dataset Check:")
    try:
        from src.evaluation.dataset import (
            RAG_EVAL_CASES, BASELINE_EVAL_CASES,
            MULTIAGENT_EVAL_CASES
        )

        print(f"  ✅ RAG cases: {len(RAG_EVAL_CASES)}")
        print(f"  ✅ Baseline cases: {len(BASELINE_EVAL_CASES)}")
        print(f"  ✅ Multi-agent cases: {len(MULTIAGENT_EVAL_CASES)}")

        # Validate structure
        for case in RAG_EVAL_CASES:
            assert "id" in case
            assert "input" in case
            assert "expected" in case
        print(f"  ✅ All cases have correct structure")

    except Exception as e:
        print(f"  ❌ Dataset check failed: {e}")
        all_good = False

    # Test 4: Single baseline evaluation
    print("\n🔄 Single Eval Run Check:")
    try:
        from src.evaluation.evaluator import run_baseline
        from src.evaluation.scorer import score_response
        from src.evaluation.models import ExpectedOutput

        answer, sources, latency = await run_baseline(
            "What is a Python list comprehension?"
        )

        score = score_response(
            actual_answer=answer,
            expected=ExpectedOutput(
                must_contain=["python", "list"],
                should_contain=["comprehension"],
                min_length=20,
            ),
        )

        print(f"  ✅ Baseline ran in {latency:.2f}s")
        print(f"  ✅ Answer: {answer[:60]}...")
        print(f"  ✅ Score: {score.total_score:.3f}")
        print(f"  ✅ Passed: {score.passed}")

    except Exception as e:
        print(f"  ❌ Single eval failed: {e}")
        all_good = False

    # Test 5: Mini evaluation suite
    print("\n📊 Mini Eval Suite Check:")
    try:
        from src.evaluation.evaluator import evaluate_system, run_baseline
        from src.evaluation.dataset import BASELINE_EVAL_CASES

        # Run just 2 cases as a quick test
        mini_cases = BASELINE_EVAL_CASES[:2]
        summary = await evaluate_system(
            system_name="Mini-Baseline-Test",
            cases=mini_cases,
            runner_func=run_baseline,
        )

        print(f"  ✅ Summary created")
        print(f"  ✅ Total cases: {summary.total_cases}")
        print(f"  ✅ Passed: {summary.passed_cases}")
        print(f"  ✅ Avg score: {summary.avg_score:.3f}")
        print(f"  ✅ Pass rate: {summary.pass_rate:.1%}")
        print(f"  ✅ Avg latency: {summary.avg_latency:.2f}s")

    except Exception as e:
        print(f"  ❌ Mini eval suite failed: {e}")
        all_good = False

    print("\n" + "=" * 50)
    if all_good:
        print("✅ Step 8 Complete! Ready for Step 9 (CLI Interface)")
    else:
        print("❌ Fix errors above before Step 9")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(verify())