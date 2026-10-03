import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from backend.app.db.session import Base
from backend.app.models.types import VectorType

class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(String(36), ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_path = Column(String(1024), nullable=False, index=True)
    language = Column(String(50), nullable=True, index=True)
    symbol_name = Column(String(255), nullable=True, index=True)
    symbol_type = Column(String(50), nullable=True, index=True) # function, class, method, module, doc
    chunk_type = Column(String(50), default="code", index=True) # code, markdown, config
    
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=True)
    
    # Vector embedding column (pgvector Vector or JSON fallback)
    embedding = Column(VectorType, nullable=True)
    
    chunk_metadata = Column("metadata", JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repository = relationship("Repository", back_populates="chunks")
    file = relationship("RepositoryFile", back_populates="chunks")

class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String(50), default="hybrid") # hybrid, vector, bm25
    candidates_count = Column(Integer, default=0)
    top_chunk_ids = Column(JSON, default=list)
    scores = Column(JSON, default=dict)
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
