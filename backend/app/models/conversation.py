import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Chat")
    summary = Column(Text, nullable=True) # Context-aware conversation summarization
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    agent_runs = relationship("AgentRun", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Grounding & Citations metadata: [{file_path, start_line, end_line, symbol_name, snippet}]
    citations = Column(JSON, default=list)
    agent_name = Column(String(50), nullable=True)
    intent = Column(String(50), nullable=True)
    
    # Latency & Token metrics
    retrieval_latency_ms = Column(Float, nullable=True)
    generation_latency_ms = Column(Float, nullable=True)
    token_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_type = Column(String(50), nullable=False) # CodeAgent, DebugAgent, SecurityAgent, etc.
    status = Column(String(50), default="RUNNING") # RUNNING, COMPLETED, FAILED
    input_query = Column(Text, nullable=False)
    output_response = Column(Text, nullable=True)
    intermediate_steps = Column(JSON, default=list) # tool calls, observation logs
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="agent_runs")
