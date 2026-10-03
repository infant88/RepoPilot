import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from backend.app.db.session import Base

class EvaluationDataset(Base):
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # List of test items: [{"id": "...", "question": "...", "expected_answer": "...", "expected_sources": [...]}]
    test_cases = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # RAG Metrics (0.0 to 1.0)
    context_precision = Column(Float, default=0.0)
    context_recall = Column(Float, default=0.0)
    answer_relevance = Column(Float, default=0.0)
    faithfulness = Column(Float, default=0.0)
    
    # Latency & Cost Metrics
    retrieval_latency_ms = Column(Float, default=0.0)
    generation_latency_ms = Column(Float, default=0.0)
    total_latency_ms = Column(Float, default=0.0)
    total_token_usage = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    
    # Detailed case results
    case_results = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
