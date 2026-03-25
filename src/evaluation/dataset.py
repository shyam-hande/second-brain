# src/evaluation/dataset.py
"""
Test cases for evaluating the second brain system.

Three sets of cases:
1. RAG evaluation cases (knowledge base queries)
2. Memory evaluation cases (personalization)
3. Multi-agent evaluation cases (complex queries)
"""
from src.evaluation.models import QueryInput, ExpectedOutput


# ── RAG Evaluation Cases ───────────────────────────────────────────────────────
RAG_EVAL_CASES = [
    {
        "id": "rag_001",
        "input": QueryInput(
            query="What ingredients do I need for carbonara?",
            category="recipe",
        ),
        "expected": ExpectedOutput(
            must_contain=["pasta", "egg"],
            should_contain=["guanciale", "pecorino", "pepper"],
            should_use_sources=True,
            min_length=50,
        ),
    },
    {
        "id": "rag_002",
        "input": QueryInput(
            query="How do I make carbonara without cream?",
            category="recipe",
        ),
        "expected": ExpectedOutput(
            must_contain=["egg", "cream"],
            should_contain=["pecorino", "guanciale", "pasta water"],
            must_not_contain=[],
            should_use_sources=True,
            min_length=50,
        ),
    },
    {
        "id": "rag_003",
        "input": QueryInput(
            query="What Python tips do I have?",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["python"],
            should_contain=["list", "comprehension", "f-string"],
            should_use_sources=True,
            min_length=30,
        ),
    },
    {
        "id": "rag_004",
        "input": QueryInput(
            query="Tell me about the walrus operator",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["walrus", ":="],
            should_contain=["assign", "operator"],
            should_use_sources=True,
            min_length=30,
        ),
    },
    {
        "id": "rag_005",
        "input": QueryInput(
            query="What is the best way to create virtual environments?",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["venv"],
            should_contain=["python", "virtual"],
            should_use_sources=True,
            min_length=20,
        ),
    },
]


# ── Multi-Agent Evaluation Cases ───────────────────────────────────────────────
MULTIAGENT_EVAL_CASES = [
    {
        "id": "ma_001",
        "input": QueryInput(
            query="What pasta recipes do I have and what makes them special?",
            category="recipe",
        ),
        "expected": ExpectedOutput(
            must_contain=["carbonara", "pasta"],
            should_contain=["egg", "guanciale", "cream"],
            should_use_sources=True,
            min_length=80,
        ),
    },
    {
        "id": "ma_002",
        "input": QueryInput(
            query="Give me a summary of my Python programming notes",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["python"],
            should_contain=["list", "comprehension", "venv", "f-string"],
            should_use_sources=True,
            min_length=80,
        ),
    },
    {
        "id": "ma_003",
        "input": QueryInput(
            query="What cooking tips do I have in my knowledge base?",
            category="recipe",
        ),
        "expected": ExpectedOutput(
            must_contain=["pasta", "carbonara"],
            should_contain=["ingredient", "cook"],
            should_use_sources=True,
            min_length=50,
        ),
    },
]


# ── Baseline Evaluation Cases (same questions, no RAG) ────────────────────────
# These are the same questions but we expect WORSE results
# because the agent has no access to personal notes
BASELINE_EVAL_CASES = [
    {
        "id": "base_001",
        "input": QueryInput(
            query="What ingredients do I need for carbonara?",
            category="recipe",
        ),
        "expected": ExpectedOutput(
            must_contain=["pasta", "egg"],
            should_contain=["guanciale", "cheese"],
            should_use_sources=False,  # baseline won't have sources
            min_length=50,
        ),
    },
    {
        "id": "base_002",
        "input": QueryInput(
            query="What Python tips do I have?",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["python"],
            should_contain=["list", "comprehension"],
            should_use_sources=False,
            min_length=30,
        ),
    },
    {
        "id": "base_003",
        "input": QueryInput(
            query="Tell me about the walrus operator",
            category="coding",
        ),
        "expected": ExpectedOutput(
            must_contain=["walrus", ":="],
            should_contain=["assign"],
            should_use_sources=False,
            min_length=30,
        ),
    },
]