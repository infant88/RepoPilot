import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.repository import RepositoryFile, Issue, PullRequest
from backend.app.models.chunk import CodeChunk
from backend.app.rag.retriever import HybridRetriever
from backend.app.rag.reranker import reranker_service

logger = logging.getLogger(__name__)

class RepositoryTools:
    def __init__(self, session: AsyncSession, repository_id: str):
        self.session = session
        self.repository_id = repository_id
        self.retriever = HybridRetriever(session)

    async def semantic_code_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search code chunks using hybrid vector + BM25 retrieval and reranking."""
        candidates = await self.retriever.retrieve(
            query=query,
            repository_id=self.repository_id,
            top_candidates=25,
        )
        reranked = reranker_service.rerank(query, candidates, top_k=top_k)
        return [
            {
                "file_path": r.chunk.file_path,
                "start_line": r.chunk.start_line,
                "end_line": r.chunk.end_line,
                "symbol_name": r.chunk.symbol_name,
                "symbol_type": r.chunk.symbol_type,
                "score": r.rerank_score,
                "code": r.chunk.content,
            }
            for r in reranked
        ]

    async def get_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve complete content and metadata of a file."""
        stmt = select(RepositoryFile).where(
            RepositoryFile.repository_id == self.repository_id,
            RepositoryFile.path == path,
        )
        res = await self.session.execute(stmt)
        f = res.scalar_one_or_none()
        if not f:
            return None
        return {
            "path": f.path,
            "language": f.language,
            "size_bytes": f.size_bytes,
            "content": f.content,
        }

    async def get_file_lines(self, path: str, start_line: int, end_line: int) -> Optional[str]:
        """Retrieve a specific line window from a file."""
        f = await self.get_file(path)
        if not f or not f.get("content"):
            return None
        lines = f["content"].splitlines()
        s = max(0, start_line - 1)
        e = min(len(lines), end_line)
        return "\n".join(lines[s:e])

    async def get_repository_structure(self) -> List[Dict[str, Any]]:
        """Get listing of all indexed files in the repository."""
        stmt = select(RepositoryFile).where(RepositoryFile.repository_id == self.repository_id)
        res = await self.session.execute(stmt)
        files = res.scalars().all()
        return [
            {"path": f.path, "language": f.language, "size_bytes": f.size_bytes}
            for f in files
        ]

    async def get_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Search for specific functions, classes, or symbols across the codebase."""
        stmt = select(CodeChunk).where(
            CodeChunk.repository_id == self.repository_id,
            CodeChunk.symbol_name.ilike(f"%{symbol_name}%"),
        )
        res = await self.session.execute(stmt)
        chunks = res.scalars().all()
        return [
            {
                "file_path": c.file_path,
                "symbol_name": c.symbol_name,
                "symbol_type": c.symbol_type,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "content": c.content,
            }
            for c in chunks
        ]

    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search repository issues."""
        stmt = select(Issue).where(
            Issue.repository_id == self.repository_id,
            Issue.title.ilike(f"%{query}%"),
        )
        res = await self.session.execute(stmt)
        issues = res.scalars().all()
        return [{"number": i.number, "title": i.title, "state": i.state, "body": i.body} for i in issues]

    async def search_pull_requests(self, query: str) -> List[Dict[str, Any]]:
        """Search repository pull requests."""
        stmt = select(PullRequest).where(
            PullRequest.repository_id == self.repository_id,
            PullRequest.title.ilike(f"%{query}%"),
        )
        res = await self.session.execute(stmt)
        prs = res.scalars().all()
        return [{"number": p.number, "title": p.title, "state": p.state, "body": p.body} for p in prs]
