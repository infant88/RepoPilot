import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db, get_session_context
from backend.app.models.repository import Repository, RepositoryFile, RepositoryBranch
from backend.app.schemas.repository import (
    RepositoryCreate,
    RepositoryResponse,
    IndexStatusResponse,
    RepositoryFileResponse,
    FileTreeNode,
)
from backend.app.github.service import GitHubIngestionService

router = APIRouter(prefix="/repositories", tags=["repositories"])

async def _run_indexing_background(repository_id: str, branch: Optional[str] = None):
    async with get_session_context() as session:
        service = GitHubIngestionService(session)
        await service.ingest_repository(repository_id, branch)

@router.post("", response_model=RepositoryResponse)
async def create_repository(
    payload: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Register and initiate indexing for a GitHub or local repository."""
    service = GitHubIngestionService(db)
    owner, repo_name = service.parse_repo_url(payload.url)
    full_name = f"{owner}/{repo_name}"

    # Check existing
    stmt = select(Repository).where(Repository.full_name == full_name)
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        # Trigger re-index in background
        background_tasks.add_task(_run_indexing_background, existing.id, payload.branch)
        return existing

    repo = Repository(
        name=repo_name,
        owner=owner,
        full_name=full_name,
        html_url=payload.url,
        default_branch=payload.branch or "main",
        current_branch=payload.branch or "main",
        status="QUEUED",
        status_message="Indexing job queued in background worker...",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    # Launch background indexing
    background_tasks.add_task(_run_indexing_background, repo.id, payload.branch)
    return repo

@router.get("", response_model=List[RepositoryResponse])
async def list_repositories(db: AsyncSession = Depends(get_db)):
    """List all registered repositories."""
    stmt = select(Repository).order_by(Repository.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{id}", response_model=RepositoryResponse)
async def get_repository(id: str, db: AsyncSession = Depends(get_db)):
    """Get single repository details and status."""
    stmt = select(Repository).where(Repository.id == id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.post("/{id}/index", response_model=IndexStatusResponse)
async def trigger_index(
    id: str,
    background_tasks: BackgroundTasks,
    branch: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger manual re-indexing."""
    stmt = select(Repository).where(Repository.id == id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.status = "QUEUED"
    repo.status_message = "Indexing requested..."
    repo.progress_percentage = 0
    if branch:
        repo.current_branch = branch
    await db.commit()

    background_tasks.add_task(_run_indexing_background, repo.id, repo.current_branch)
    return IndexStatusResponse(
        repository_id=repo.id,
        status=repo.status,
        status_message=repo.status_message,
        progress_percentage=repo.progress_percentage,
        total_files=repo.total_files,
        total_chunks=repo.total_chunks,
    )

@router.get("/{id}/index-status", response_model=IndexStatusResponse)
async def get_index_status(id: str, db: AsyncSession = Depends(get_db)):
    """Poll indexing progress and status."""
    stmt = select(Repository).where(Repository.id == id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    return IndexStatusResponse(
        repository_id=repo.id,
        status=repo.status,
        status_message=repo.status_message,
        progress_percentage=repo.progress_percentage,
        total_files=repo.total_files,
        total_chunks=repo.total_chunks,
    )

@router.get("/{id}/files", response_model=List[RepositoryFileResponse])
async def list_files(id: str, db: AsyncSession = Depends(get_db)):
    """List all indexed files for a repository."""
    stmt = select(RepositoryFile).where(RepositoryFile.repository_id == id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{id}/files-tree", response_model=List[FileTreeNode])
async def get_file_tree(id: str, db: AsyncSession = Depends(get_db)):
    """Hierarchical file tree for frontend sidebar explorer."""
    stmt = select(RepositoryFile).where(RepositoryFile.repository_id == id)
    res = await db.execute(stmt)
    files = res.scalars().all()

    # Build tree
    root_nodes: Dict[str, Any] = {}
    for f in files:
        parts = f.path.split("/")
        curr = root_nodes
        for i, part in enumerate(parts):
            is_file = (i == len(parts) - 1)
            if part not in curr:
                curr[part] = {
                    "name": part,
                    "path": "/".join(parts[: i + 1]),
                    "type": "file" if is_file else "directory",
                    "language": f.language if is_file else None,
                    "children": {} if not is_file else None,
                }
            if not is_file:
                curr = curr[part]["children"]

    def _convert_to_list(d: Dict[str, Any]) -> List[FileTreeNode]:
        node_list = []
        for v in d.values():
            children = _convert_to_list(v["children"]) if v["children"] is not None else None
            node_list.append(
                FileTreeNode(
                    name=v["name"],
                    path=v["path"],
                    type=v["type"],
                    language=v["language"],
                    children=children,
                )
            )
        return sorted(node_list, key=lambda x: (x.type == "file", x.name))

    return _convert_to_list(root_nodes)

@router.get("/{id}/files-content")
async def get_file_content(id: str, path: str, db: AsyncSession = Depends(get_db)):
    """Get single file raw content for Monaco Editor."""
    stmt = select(RepositoryFile).where(
        RepositoryFile.repository_id == id,
        RepositoryFile.path == path,
    )
    res = await db.execute(stmt)
    f = res.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    return {
        "path": f.path,
        "language": f.language,
        "content": f.content,
        "size_bytes": f.size_bytes,
    }
