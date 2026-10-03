import logging
import time
from typing import Dict, Any, List, Optional, TypedDict
from sqlalchemy.ext.asyncio import AsyncSession
from langgraph.graph import StateGraph, END

from backend.app.rag.query_understanding import query_understanding_engine
from backend.app.tools.registry import RepositoryTools
from backend.app.rag.context_builder import context_builder
from backend.app.rag.generator import llm_service
from backend.app.schemas.chat import Citation

logger = logging.getLogger(__name__)

class AgentWorkflowState(TypedDict):
    query: str
    repository_id: str
    repository_name: str
    intent: str
    agent_type: str
    intermediate_steps: List[Dict[str, Any]]
    retrieved_evidence: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    final_response: str
    start_time: float
    execution_time_ms: float

class RepoPilotOrchestrator:
    def __init__(self, session: AsyncSession, repository_id: str, repository_name: str):
        self.session = session
        self.repository_id = repository_id
        self.repository_name = repository_name
        self.tools = RepositoryTools(session, repository_id)

    async def route_step(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Analyzes query intent and selects specialized agent."""
        query = state["query"]
        analysis = query_understanding_engine.analyze(query)
        state["intent"] = analysis.intent
        
        agent_names = {
            "debug": "DebugAgent",
            "security": "SecurityAgent",
            "architecture": "ArchitectureAgent",
            "devops": "DevOpsAgent",
            "documentation": "DocumentationAgent",
            "code": "CodeAgent",
        }
        state["agent_type"] = agent_names.get(analysis.intent, "CodeAgent")
        state["intermediate_steps"].append({
            "action": "route_query",
            "intent": analysis.intent,
            "chosen_agent": state["agent_type"],
            "rewritten_queries": analysis.rewritten_queries,
        })
        return state

    async def retrieval_step(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Executes targeted hybrid retrieval using the chosen agent's strategy."""
        query = state["query"]
        agent = state["agent_type"]
        
        # Tool execution: semantic search with rewrites
        evidence = await self.tools.semantic_code_search(query, top_k=8)
        state["retrieved_evidence"] = evidence
        
        state["intermediate_steps"].append({
            "action": "tool_execution",
            "tool": "semantic_code_search",
            "results_count": len(evidence),
            "top_files": [e["file_path"] for e in evidence[:3]],
        })
        return state

    async def synthesis_step(self, state: AgentWorkflowState) -> AgentWorkflowState:
        """Synthesizes grounded output and populates source citations."""
        # Convert evidence to citations
        citations = []
        for e in state["retrieved_evidence"]:
            c = Citation(
                file_path=e["file_path"],
                start_line=e["start_line"],
                end_line=e["end_line"],
                symbol_name=e.get("symbol_name"),
                symbol_type=e.get("symbol_type"),
                snippet=e["code"][:200],
                score=e.get("score"),
            )
            citations.append(c.model_dump())
        state["citations"] = citations

        state["execution_time_ms"] = (time.time() - state["start_time"]) * 1000.0
        return state

    def build_graph(self):
        """Constructs and compiles the LangGraph workflow."""
        workflow = StateGraph(AgentWorkflowState)

        workflow.add_node("router", self.route_step)
        workflow.add_node("retriever", self.retrieval_step)
        workflow.add_node("synthesizer", self.synthesis_step)

        workflow.set_entry_point("router")
        workflow.add_edge("router", "retriever")
        workflow.add_edge("retriever", "synthesizer")
        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    async def run(self, query: str) -> AgentWorkflowState:
        graph = self.build_graph()
        initial_state: AgentWorkflowState = {
            "query": query,
            "repository_id": self.repository_id,
            "repository_name": self.repository_name,
            "intent": "",
            "agent_type": "",
            "intermediate_steps": [],
            "retrieved_evidence": [],
            "citations": [],
            "final_response": "",
            "start_time": time.time(),
            "execution_time_ms": 0.0,
        }
        final_state = await graph.ainvoke(initial_state)
        return final_state
