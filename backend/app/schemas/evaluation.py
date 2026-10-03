from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class TestCaseSchema(BaseModel):
    id: Optional[str] = None
    question: str
    expected_answer: Optional[str] = None
    expected_sources: List[str] = [] # list of expected file paths

class EvaluationDatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repository_id: Optional[str] = None
    test_cases: List[TestCaseSchema]

class EvaluationRunRequest(BaseModel):
    repository_id: str
    dataset_id: Optional[str] = None
    custom_test_cases: Optional[List[TestCaseSchema]] = None

class TestCaseResult(BaseModel):
    question: str
    generated_answer: str
    retrieved_sources: List[str]
    expected_sources: List[str]
    context_precision: float
    context_recall: float
    answer_relevance: float
    faithfulness: float
    latency_ms: float
    is_grounded: bool

class EvaluationResultResponse(BaseModel):
    id: str
    repository_id: str
    dataset_id: Optional[str] = None
    context_precision: float
    context_recall: float
    answer_relevance: float
    faithfulness: float
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_latency_ms: float
    total_token_usage: int
    estimated_cost_usd: float
    case_results: List[TestCaseResult] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
