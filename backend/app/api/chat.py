import json
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db, get_session_context
from backend.app.models.repository import Repository
from backend.app.models.conversation import Conversation, Message
from backend.app.schemas.chat import (
    ChatRequest,
    MessageResponse,
    ConversationResponse,
    Citation,
)
from backend.app.rag.query_understanding import query_understanding_engine
from backend.app.rag.retriever import HybridRetriever
from backend.app.rag.reranker import reranker_service
from backend.app.rag.context_builder import context_builder
from backend.app.rag.generator import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/stream")
async def chat_stream(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Streams LLM tokens, citations, and agent status over Server-Sent Events (SSE).
    """
    # 1. Fetch Repository
    stmt = select(Repository).where(Repository.id == payload.repository_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 2. Get or create conversation
    conv_id = payload.conversation_id
    if not conv_id:
        conv = Conversation(repository_id=repo.id, title=payload.message[:40])
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        conv_id = conv.id

    # Record User Message
    user_msg = Message(conversation_id=conv_id, role="user", content=payload.message)
    db.add(user_msg)
    await db.commit()

    async def sse_event_generator():
        yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conv_id})}\n\n"

        # 1. Query Understanding & Routing
        t_start = time.time()
        analysis = query_understanding_engine.analyze(payload.message)
        agent_names = {
            "debug": "Debug Agent",
            "security": "Security Agent",
            "architecture": "Architecture Agent",
            "devops": "DevOps Agent",
            "documentation": "Documentation Agent",
            "code": "Code Agent",
        }
        agent_name = payload.agent_preference or agent_names.get(analysis.intent, "Code Agent")
        
        yield f"data: {json.dumps({'type': 'agent_status', 'agent': agent_name, 'intent': analysis.intent, 'message': f'Routing to {agent_name}...'})}\n\n"

        # 2. Hybrid Retrieval
        async with get_session_context() as session:
            retriever = HybridRetriever(session)
            # Search with rewritten queries
            candidates = await retriever.retrieve(
                query=payload.message,
                repository_id=payload.repository_id,
                filters=payload.filters,
                top_candidates=35,
            )

            # 3. Reranker
            yield f"data: {json.dumps({'type': 'agent_status', 'agent': agent_name, 'message': f'Reranking {len(candidates)} candidate chunks...'})}\n\n"
            reranked = reranker_service.rerank(payload.message, candidates, top_k=8)
            t_retrieval_ms = (time.time() - t_start) * 1000.0

            # 4. Context Builder
            built_ctx = context_builder.build_context(repo.full_name, payload.message, reranked)

            # Yield Citations to Frontend immediately
            citations_data = [c.model_dump() for c in built_ctx.citations]
            yield f"data: {json.dumps({'type': 'citations', 'citations': citations_data, 'retrieval_latency_ms': round(t_retrieval_ms, 2)})}\n\n"

            # 5. LLM Streaming
            t_gen_start = time.time()
            accumulated_tokens = []
            async for chunk in llm_service.generate_response_stream(
                query=payload.message,
                built_context=built_ctx,
                agent_name=agent_name,
            ):
                if chunk.get("type") == "token":
                    accumulated_tokens.append(chunk["content"])
                    yield f"data: {json.dumps(chunk)}\n\n"

            t_gen_ms = (time.time() - t_gen_start) * 1000.0
            full_content = "".join(accumulated_tokens)

            # 6. Save Assistant Message in DB
            asst_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content=full_content,
                citations=citations_data,
                agent_name=agent_name,
                intent=analysis.intent,
                retrieval_latency_ms=round(t_retrieval_ms, 2),
                generation_latency_ms=round(t_gen_ms, 2),
                token_count=len(full_content.split()) * 2,
            )
            session.add(asst_msg)
            await session.commit()

            yield f"data: {json.dumps({'type': 'done', 'message_id': asst_msg.id})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    repository_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations for a repository."""
    stmt = (
        select(Conversation)
        .where(Conversation.repository_id == repository_id)
        .order_by(Conversation.updated_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/conversations/{id}", response_model=ConversationResponse)
async def get_conversation(id: str, db: AsyncSession = Depends(get_db)):
    """Fetch single conversation with complete message history."""
    stmt = select(Conversation).where(Conversation.id == id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.delete("/conversations/{id}")
async def clear_conversation(id: str, db: AsyncSession = Depends(get_db)):
    """Clear conversation history."""
    stmt = select(Conversation).where(Conversation.id == id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await db.delete(conv)
    await db.commit()
    return {"status": "success", "message": "Conversation deleted"}
