import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.db.session import get_db, get_session_context
from backend.app.models.repository import Repository
from backend.app.github.service import GitHubIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["github"])

def _verify_webhook_signature(payload_body: bytes, secret: str, signature_header: str) -> bool:
    """Verifies GitHub HMAC-SHA256 webhook signature."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    given = signature_header.split("sha256=")[1]
    return hmac.compare_digest(expected, given)

async def _process_incremental_webhook(repo_full_name: str, branch: str):
    async with get_session_context() as session:
        stmt = select(Repository).where(Repository.full_name == repo_full_name)
        res = await session.execute(stmt)
        repo = res.scalar_one_or_none()
        if repo:
            logger.info(f"Triggering incremental re-index for {repo_full_name} on branch {branch}")
            service = GitHubIngestionService(session)
            await service.ingest_repository(repo.id, branch)

@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None),
):
    """
    Receives GitHub push/commit webhook events, verifies HMAC signature,
    and dispatches incremental re-indexing.
    """
    body = await request.body()

    if settings.GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
        if not _verify_webhook_signature(body, settings.GITHUB_WEBHOOK_SECRET, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()

    if x_github_event == "push":
        ref = payload.get("ref", "") # e.g. refs/heads/main
        branch = ref.replace("refs/heads/", "")
        repo_data = payload.get("repository", {})
        full_name = repo_data.get("full_name")

        if full_name:
            background_tasks.add_task(_process_incremental_webhook, full_name, branch)
            return {
                "status": "accepted",
                "message": f"Incremental indexing queued for {full_name}:{branch}",
            }

    return {"status": "ignored", "event": x_github_event}
