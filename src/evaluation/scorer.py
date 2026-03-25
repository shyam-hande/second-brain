# src/evaluation/scorer.py
"""
Scores actual agent outputs against expected outputs.
Returns numeric scores between 0 and 1.
"""
from src.evaluation.models import ExpectedOutput, EvalScore
import logfire


def score_response(
    actual_answer: str,
    expected: ExpectedOutput,
    sources_used: list[str] = None,
) -> EvalScore:
    """
    Score an actual response against expected output.

    Scoring breakdown:
    - must_contain:   40% weight (critical requirements)
    - should_contain: 30% weight (nice to have)
    - length:         15% weight (not too short)
    - sources:        15% weight (cited sources if needed)
    """
    sources_used = sources_used or []
    answer_lower = actual_answer.lower()
    details = {}

    # ── Score 1: Must contain (40% weight) ────────────────────────
    if expected.must_contain:
        hits = [
            word for word in expected.must_contain
            if word.lower() in answer_lower
        ]
        must_score = len(hits) / len(expected.must_contain)
        details["must_contain_hits"] = hits
        details["must_contain_misses"] = [
            w for w in expected.must_contain
            if w.lower() not in answer_lower
        ]
    else:
        must_score = 1.0  # no requirements = full score
        details["must_contain_hits"] = []

    # ── Score 2: Should contain (30% weight) ──────────────────────
    if expected.should_contain:
        hits = [
            word for word in expected.should_contain
            if word.lower() in answer_lower
        ]
        should_score = len(hits) / len(expected.should_contain)
        details["should_contain_hits"] = hits
    else:
        should_score = 1.0
        details["should_contain_hits"] = []

    # ── Score 3: Length check (15% weight) ────────────────────────
    if len(actual_answer) >= expected.min_length:
        length_score = 1.0
    else:
        length_score = len(actual_answer) / expected.min_length
    details["answer_length"] = len(actual_answer)
    details["min_required"] = expected.min_length

    # ── Score 4: Source usage (15% weight) ────────────────────────
    if expected.should_use_sources:
        source_score = 1.0 if sources_used else 0.0
        details["sources_found"] = sources_used
    else:
        source_score = 1.0  # not required = full score
        details["sources_found"] = sources_used

    # ── Must not contain check (penalty) ──────────────────────────
    penalty = 0.0
    if expected.must_not_contain:
        violations = [
            word for word in expected.must_not_contain
            if word.lower() in answer_lower
        ]
        if violations:
            penalty = 0.3 * (len(violations) / len(expected.must_not_contain))
            details["violations"] = violations

    # ── Calculate total score ──────────────────────────────────────
    total = (
        (must_score * 0.40) +
        (should_score * 0.30) +
        (length_score * 0.15) +
        (source_score * 0.15)
    ) - penalty

    total = max(0.0, min(1.0, total))  # clamp to [0, 1]
    passed = total >= 0.7 and must_score >= 0.8

    score = EvalScore(
        total_score=round(total, 3),
        must_contain_score=round(must_score, 3),
        should_contain_score=round(should_score, 3),
        length_score=round(length_score, 3),
        source_score=round(source_score, 3),
        passed=passed,
        details=details,
    )

    logfire.info(
        "response_scored",
        total=total,
        passed=passed,
        must_score=must_score,
    )

    return score