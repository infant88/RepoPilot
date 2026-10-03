import os
import hashlib
import logging
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.repository import Repository, RepositoryBranch, RepositoryFile
from backend.app.models.chunk import CodeChunk
from backend.app.rag.chunker import CodeAwareChunker
from backend.app.rag.embeddings import embedding_service

logger = logging.getLogger(__name__)

class GitHubIngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunker = CodeAwareChunker()
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoPilot/1.0",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    def parse_repo_url(self, url: str) -> tuple[str, str]:
        """Extracts owner and repo name from GitHub URL or local path."""
        url = url.strip().rstrip("/")
        if "github.com" in url:
            parts = url.split("github.com/")[1].split("/")
            return parts[0], parts[1]
        # Local or named repo
        base = os.path.basename(url) or "sample-repo"
        return "local", base

    async def ingest_repository(self, repository_id: str, branch: Optional[str] = None):
        """
        Executes full repository ingestion lifecycle:
        QUEUED -> SCANNING -> PARSING -> CHUNKING -> EMBEDDING -> INDEXING -> COMPLETED
        """
        stmt = select(Repository).where(Repository.id == repository_id)
        res = await self.session.execute(stmt)
        repo = res.scalar_one_or_none()
        if not repo:
            logger.error(f"Repository {repository_id} not found")
            return

        target_branch = branch or repo.current_branch or "main"

        try:
            # 1. SCANNING
            repo.status = "SCANNING"
            repo.status_message = "Scanning repository tree and file inventory..."
            repo.progress_percentage = 15
            await self.session.commit()

            files_to_index: List[Dict[str, Any]] = []

            # Check if this is a local path or GitHub remote
            if repo.html_url.startswith("http") and "github.com" in repo.html_url:
                files_to_index = await self._scan_github_tree(repo.owner, repo.name, target_branch)
            else:
                # Local directory scan (e.g. examples/sample-repo)
                local_dir = repo.html_url if os.path.exists(repo.html_url) else os.path.join(os.getcwd(), repo.html_url)
                if not os.path.exists(local_dir):
                    # Check relative to RepoPilot
                    local_dir = os.path.join(os.getcwd(), "examples", "sample-repo")
                files_to_index = self._scan_local_directory(local_dir)

            repo.total_files = len(files_to_index)
            repo.status = "PARSING"
            repo.status_message = f"Found {len(files_to_index)} files. Parsing AST and logical chunks..."
            repo.progress_percentage = 35
            await self.session.commit()

            # 2. PARSING & CHUNKING
            total_chunks = 0
            chunks_to_insert: List[CodeChunk] = []
            files_db_map = {}

            for f_data in files_to_index:
                rel_path = f_data["path"]
                content = f_data["content"]
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                # Upsert RepositoryFile
                file_stmt = select(RepositoryFile).where(
                    RepositoryFile.repository_id == repo.id,
                    RepositoryFile.path == rel_path,
                )
                file_res = await self.session.execute(file_stmt)
                db_file = file_res.scalar_one_or_none()

                lang = self.chunker.detect_language(rel_path)

                if not db_file:
                    db_file = RepositoryFile(
                        repository_id=repo.id,
                        path=rel_path,
                        name=os.path.basename(rel_path),
                        extension=os.path.splitext(rel_path)[1],
                        language=lang,
                        size_bytes=len(content.encode("utf-8")),
                        content_hash=content_hash,
                        content=content,
                    )
                    self.session.add(db_file)
                    await self.session.flush()
                else:
                    # Check for incremental update
                    if db_file.content_hash == content_hash:
                        # Unchanged file - skip rechunking if chunks exist
                        chk_check = await self.session.execute(
                            select(CodeChunk.id).where(CodeChunk.file_id == db_file.id)
                        )
                        if chk_check.first():
                            files_db_map[rel_path] = db_file
                            continue

                    db_file.content_hash = content_hash
                    db_file.content = content
                    db_file.size_bytes = len(content.encode("utf-8"))
                    # Delete obsolete chunks for this file
                    await self.session.execute(
                        delete(CodeChunk).where(CodeChunk.file_id == db_file.id)
                    )

                files_db_map[rel_path] = db_file

                # Generate code-aware chunks
                raw_chunks = self.chunker.chunk_file(content, rel_path)
                for rc in raw_chunks:
                    chunk_obj = CodeChunk(
                        repository_id=repo.id,
                        file_id=db_file.id,
                        file_path=rel_path,
                        language=lang,
                        symbol_name=rc.symbol_name,
                        symbol_type=rc.symbol_type,
                        chunk_type=rc.chunk_type,
                        start_line=rc.start_line,
                        end_line=rc.end_line,
                        content=rc.content,
                        content_hash=rc.content_hash,
                        commit_hash=target_branch,
                        chunk_metadata=rc.metadata,
                    )
                    chunks_to_insert.append(chunk_obj)
                    total_chunks += 1

            # 3. EMBEDDING GENERATION
            repo.status = "EMBEDDING"
            repo.status_message = f"Generating vector embeddings for {len(chunks_to_insert)} code chunks..."
            repo.progress_percentage = 65
            await self.session.commit()

            if chunks_to_insert:
                texts = [
                    f"{c.file_path} {c.symbol_name or ''} {c.content}"
                    for c in chunks_to_insert
                ]
                embeddings = await embedding_service.get_embeddings(texts)
                for idx, chunk_obj in enumerate(chunks_to_insert):
                    chunk_obj.embedding = embeddings[idx]
                    self.session.add(chunk_obj)

            # 4. INDEXING COMPLETE
            repo.status = "INDEXING"
            repo.status_message = "Writing vector indexes and updating stats..."
            repo.progress_percentage = 90
            await self.session.commit()

            # Count total chunks
            count_stmt = select(CodeChunk).where(CodeChunk.repository_id == repo.id)
            all_chunks = (await self.session.execute(count_stmt)).scalars().all()
            repo.total_chunks = len(all_chunks)

            # Compute language breakdown
            lang_counts = {}
            for c in all_chunks:
                lang = c.language or "other"
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
            repo.language_breakdown = lang_counts

            repo.status = "COMPLETED"
            repo.status_message = "Repository indexed successfully. Ready for queries!"
            repo.progress_percentage = 100
            await self.session.commit()
            logger.info(f"Repository {repo.full_name} indexed: {repo.total_files} files, {repo.total_chunks} chunks.")

        except Exception as e:
            logger.exception(f"Repository ingestion error: {e}")
            repo.status = "FAILED"
            repo.status_message = f"Indexing failed: {str(e)}"
            await self.session.commit()

    async def _scan_github_tree(self, owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
        """Scans GitHub REST API recursive git tree and downloads text source files."""
        files = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Fetch branch commit
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            res = await client.get(url, headers=self.headers)
            if res.status_code == 404:
                # Query repo info to discover actual default branch (e.g. main vs master)
                info_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=self.headers)
                if info_res.status_code == 200:
                    real_branch = info_res.json().get("default_branch", "main")
                    if real_branch != branch:
                        branch = real_branch
                        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
                        res = await client.get(url, headers=self.headers)

            if res.status_code != 200:
                logger.warning(f"GitHub tree fetch failed ({res.status_code} for {owner}/{repo}:{branch}), falling back to sample repo")
                return self._scan_local_directory(os.path.join(os.getcwd(), "examples", "sample-repo"))

            data = res.json()
            tree = data.get("tree", [])

            # Filter relevant source files
            for item in tree:
                path = item.get("path", "")
                if item.get("type") == "blob" and self._is_supported_source_file(path):
                    # Fetch blob content
                    blob_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                    file_res = await client.get(blob_url, headers=self.headers)
                    if file_res.status_code == 200:
                        files.append({"path": path, "content": file_res.text})
                    if len(files) >= 50:  # Bound initial ingest
                        break
        return files

    def _scan_local_directory(self, base_dir: str) -> List[Dict[str, Any]]:
        """Scans local filesystem directory for code files."""
        results = []
        ignore_dirs = {".git", "node_modules", "venv", "__pycache__", ".next", "dist", "build"}

        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), base_dir).replace("\\", "/")
                if self._is_supported_source_file(rel_path):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            results.append({"path": rel_path, "content": f.read()})
                    except Exception as e:
                        logger.warning(f"Could not read {full_path}: {e}")
        return results

    def _is_supported_source_file(self, path: str) -> bool:
        lower = path.lower()
        if any(ign in lower for ign in ["package-lock.json", "yarn.lock", ".min.js", ".pyc"]):
            return False
        valid_exts = [
            ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
            ".cpp", ".c", ".h", ".md", ".yml", ".yaml", ".json", ".sh",
        ]
        return any(lower.endswith(ext) for ext in valid_exts) or "dockerfile" in lower
