from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None

class ChatRequest(BaseModel):
    repository_id: str
    message: str
    conversation_id: Optional[str] = None
    agent_preference: Optional[str] = None # auto, code, debug, security, architecture, devops, docs
    filters: Optional[Dict[str, Any]] = None # path filter, language filter

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: List[Citation] = []
    agent_name: Optional[str] = None
    intent: Optional[str] = None
    retrieval_latency_ms: Optional[float] = None
    generation_latency_ms: Optional[float] = None
    token_count: Optional[int] = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationResponse(BaseModel):
    id: str
    repository_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)

class AgentStep(BaseModel):
    step: str
    description: str
    details: Optional[Dict[str, Any]] = None

class AgentRunResponse(BaseModel):
    id: str
    agent_type: str
    status: str
    input_query: str
    output_response: Optional[str] = None
    intermediate_steps: List[Dict[str, Any]] = []
    execution_time_ms: float
    citations: List[Citation] = []
