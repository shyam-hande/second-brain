# src/evaluation/models.py
from pydantic import BaseModel, Field


class QueryInput(BaseModel):
    """Input for a single evaluation case."""
    query: str
    context: str = ""           # optional extra context
    category: str = "general"  # factual / personal / recipe / coding


class ExpectedOutput(BaseModel):
    """What we expect a good answer to contain."""
    must_contain: list[str] = []    # these words MUST be in answer
    should_contain: list[str] = []  # these words SHOULD be in answer
    must_not_contain: list[str] = [] # these must NOT be in answer
    min_length: int = 20            # minimum answer length
    should_use_sources: bool = False # should cite sources?
    expected_confidence: str = ""   # expected confidence level


class EvalScore(BaseModel):
    """Score for a single evaluation."""
    total_score: float = Field(ge=0.0, le=1.0)
    must_contain_score: float = Field(ge=0.0, le=1.0)
    should_contain_score: float = Field(ge=0.0, le=1.0)
    length_score: float = Field(ge=0.0, le=1.0)
    source_score: float = Field(ge=0.0, le=1.0)
    passed: bool = False
    details: dict = {}


class EvalResult(BaseModel):
    """Result of running one eval case."""
    case_id: str
    query: str
    actual_answer: str
    expected: ExpectedOutput
    score: EvalScore
    system_used: str    # "baseline" / "rag" / "multiagent"
    latency_seconds: float = 0.0
    sources_used: list[str] = []


class EvalSummary(BaseModel):
    """Summary of all eval results for one system."""
    system_name: str
    total_cases: int
    passed_cases: int
    avg_score: float
    avg_latency: float
    scores_by_category: dict = {}
    pass_rate: float = 0.0