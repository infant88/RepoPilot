import os
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.core.config import settings
from backend.app.rag.generator import llm_service

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsUpdateRequest(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_base_url: Optional[str] = None

@router.get("")
async def get_settings():
    """Retrieve current LLM configuration and key status."""
    return {
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "has_api_key": bool(settings.LLM_API_KEY),
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
    }

@router.post("")
async def update_settings(payload: SettingsUpdateRequest):
    """Update LLM provider, API key, and model at runtime."""
    if payload.llm_provider:
        settings.LLM_PROVIDER = payload.llm_provider
    if payload.llm_api_key is not None:
        settings.LLM_API_KEY = payload.llm_api_key.strip() or None
    if payload.llm_model:
        settings.LLM_MODEL = payload.llm_model.strip()
    if payload.llm_base_url is not None:
        settings.LLM_BASE_URL = payload.llm_base_url.strip() or None

    # Re-initialize LLM client with new configuration
    llm_service.reinitialize()

    return {
        "status": "success",
        "message": "LLM settings updated successfully",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "llm_base_url": settings.LLM_BASE_URL,
        "has_api_key": bool(settings.LLM_API_KEY),
    }
