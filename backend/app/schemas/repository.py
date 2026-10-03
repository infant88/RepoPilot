from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, ConfigDict

class RepositoryCreate(BaseModel):
    url: str = Field(..., description="GitHub repository URL or local path")
    branch: Optional[str] = Field("main", description="Branch name to index")

class RepositoryBranchResponse(BaseModel):
    id: str
    name: str
    commit_sha: str
    is_default: bool

class RepositoryFileResponse(BaseModel):
    id: str
    path: str
    name: str
    language: Optional[str] = None
    size_bytes: int
    content_hash: str
    content: Optional[str] = None

class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str # "file" or "directory"
    language: Optional[str] = None
    children: Optional[List['FileTreeNode']] = None

class RepositoryResponse(BaseModel):
    id: str
    name: str
    owner: str
    full_name: str
    html_url: str
    description: Optional[str] = None
    default_branch: str
    current_branch: str
    status: str
    status_message: Optional[str] = None
    progress_percentage: int
    total_files: int
    total_chunks: int
    language_breakdown: Dict[str, Any]
    last_indexed_commit: Optional[str] = None
    last_indexed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IndexStatusResponse(BaseModel):
    repository_id: str
    status: str
    status_message: Optional[str] = None
    progress_percentage: int
    total_files: int
    total_chunks: int
