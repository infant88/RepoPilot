from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.models.repository import Repository
from backend.app.models.conversation import AgentRun
from backend.app.schemas.chat import AgentRunResponse
from backend.app.agents.orchestrator import RepoPilotOrchestrator

router = APIRouter(prefix="/agents", tags=["agents"])

class RunAgentRequest:
    def __init__(self, repository_id: str, query: str):
        self.repository_id = repository_id
        self.query = query

from pydantic import BaseModel
class AgentExecuteRequest(BaseModel):
    repository_id: str
    query: str
    conversation_id: str = None

@router.post("/run", response_model=AgentRunResponse)
async def run_agent(payload: AgentExecuteRequest, db: AsyncSession = Depends(get_db)):
    """Executes multi-step specialized agent workflow via LangGraph."""
    stmt = select(Repository).where(Repository.id == payload.repository_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    orchestrator = RepoPilotOrchestrator(db, repo.id, repo.full_name)
    state = await orchestrator.run(payload.query)

    # Persist agent run
    run = AgentRun(
        conversation_id=payload.conversation_id,
        agent_type=state["agent_type"],
        status="COMPLETED",
        input_query=payload.query,
        output_response=f"Executed {state['agent_type']} with {len(state['retrieved_evidence'])} evidence chunks.",
        intermediate_steps=state["intermediate_steps"],
        execution_time_ms=state["execution_time_ms"],
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    return AgentRunResponse(
        id=run.id,
        agent_type=state["agent_type"],
        status="COMPLETED",
        input_query=payload.query,
        output_response=run.output_response,
        intermediate_steps=state["intermediate_steps"],
        execution_time_ms=state["execution_time_ms"],
        citations=state["citations"],
    )
