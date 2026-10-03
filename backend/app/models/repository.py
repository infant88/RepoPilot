import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    full_name = Column(String(512), unique=True, index=True, nullable=False)
    html_url = Column(String(1024), nullable=False)
    description = Column(Text, nullable=True)
    default_branch = Column(String(100), default="main")
    current_branch = Column(String(100), default="main")
    
    # Ingestion Status: QUEUED, SCANNING, PARSING, CHUNKING, EMBEDDING, INDEXING, COMPLETED, FAILED
    status = Column(String(50), default="QUEUED", index=True)
    status_message = Column(Text, nullable=True)
    progress_percentage = Column(Integer, default=0)
    
    # Statistics
    total_files = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    language_breakdown = Column(JSON, default=dict)
    last_indexed_commit = Column(String(64), nullable=True)
    last_indexed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    branches = relationship("RepositoryBranch", back_populates="repository", cascade="all, delete-orphan")
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    chunks = relationship("CodeChunk", back_populates="repository", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="repository", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")

class RepositoryBranch(Base):
    __tablename__ = "repository_branches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    commit_sha = Column(String(64), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="branches")

class RepositoryFile(Base):
    __tablename__ = "repository_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String(1024), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    extension = Column(String(50), nullable=True)
    language = Column(String(50), nullable=True)
    size_bytes = Column(Integer, default=0)
    content_hash = Column(String(64), nullable=False)
    content = Column(Text, nullable=True)  # Stored for direct viewing/retrieval
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="files")
    chunks = relationship("CodeChunk", back_populates="file", cascade="all, delete-orphan")

class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(50), default="open")
    html_url = Column(String(1024), nullable=True)
    author = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="issues")

class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(50), default="open")
    html_url = Column(String(1024), nullable=True)
    author = Column(String(255), nullable=True)
    diff_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="pull_requests")
