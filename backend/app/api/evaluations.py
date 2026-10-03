from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.evaluation import EvaluationDataset, EvaluationResult
from backend.app.schemas.evaluation import (
    EvaluationRunRequest,
    EvaluationResultResponse,
    EvaluationDatasetCreate,
    TestCaseSchema,
)
from backend.app.evaluation.service import RAGEvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])

# Default benchmark evaluation dataset for RepoPilot
BENCHMARK_TEST_CASES = [
    TestCaseSchema(
        question="Why is the login endpoint returning 401?",
        expected_answer="Missing authorization header or invalid JWT secret token in middleware.",
        expected_sources=["backend/auth/middleware.py", "backend/config/settings.py", "backend/routes/auth.py"],
    ),
    TestCaseSchema(
        question="Explain the architecture of this repository.",
        expected_answer="FastAPI service with auth middleware, routes, and centralized config.",
        expected_sources=["backend/main.py", "backend/config/settings.py"],
    ),
    TestCaseSchema(
        question="Where is authentication implemented?",
        expected_answer="In backend/auth/middleware.py and backend/auth/jwt.py.",
        expected_sources=["backend/auth/middleware.py", "backend/auth/jwt.py"],
    ),
    TestCaseSchema(
        question="Why is Docker deployment failing for authentication?",
        expected_answer="JWT_SECRET is missing from docker-compose.yml environment variables.",
        expected_sources=["docker-compose.yml", "backend/config/settings.py"],
    ),
]

@router.post("/run", response_model=EvaluationResultResponse)
async def run_evaluation(payload: EvaluationRunRequest, db: AsyncSession = Depends(get_db)):
    """Runs automated RAG evaluation benchmarking precision, recall, and faithfulness."""
    test_cases = payload.custom_test_cases or BENCHMARK_TEST_CASES
    eval_service = RAGEvaluationService(db)
    result = await eval_service.run_evaluation(
        repository_id=payload.repository_id,
        test_cases=test_cases,
        dataset_id=payload.dataset_id,
    )
    return result

@router.get("/{id}", response_model=EvaluationResultResponse)
async def get_evaluation_result(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch specific evaluation benchmark results."""
    stmt = select(EvaluationResult).where(EvaluationResult.id == id)
    res = await db.execute(stmt)
    result = res.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation result not found")
    return result

@router.get("/repository/{repo_id}", response_model=List[EvaluationResultResponse])
async def list_repo_evaluations(repo_id: str, db: AsyncSession = Depends(get_db)):
    """List all evaluation runs for a repository."""
    stmt = (
        select(EvaluationResult)
        .where(EvaluationResult.repository_id == repo_id)
        .order_by(EvaluationResult.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
