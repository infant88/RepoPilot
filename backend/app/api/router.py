from fastapi import APIRouter
from backend.app.api.repositories import router as repositories_router
from backend.app.api.chat import router as chat_router
from backend.app.api.agents import router as agents_router
from backend.app.api.evaluations import router as evaluations_router
from backend.app.api.github import router as github_router

api_router = APIRouter()
api_router.include_router(repositories_router)
api_router.include_router(chat_router)
api_router.include_router(agents_router)
api_router.include_router(evaluations_router)
api_router.include_router(github_router)
