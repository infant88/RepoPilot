import pytest
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.query_understanding import query_understanding_engine
from backend.app.rag.reranker import reranker_service
from backend.app.rag.retriever import RetrievedCandidate
from backend.app.rag.context_builder import context_builder
from backend.app.models.chunk import CodeChunk

@pytest.mark.asyncio
async def test_embeddings_generation():
    texts = ["def authenticate_user():", "class DatabaseConnection:"]
    embeddings = await embedding_service.get_embeddings(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

def test_query_understanding_and_rewriting():
    analysis = query_understanding_engine.analyze("Why is the login endpoint returning 401?")
    assert analysis.intent == "debug"
    assert analysis.is_debugging is True
    assert any("verify_jwt_token" in q or "AuthenticationMiddleware" in q for q in analysis.rewritten_queries)

def test_reranker_and_context_builder():
    c1 = CodeChunk(
        id="c1",
        repository_id="repo1",
        file_id="f1",
        file_path="backend/auth/middleware.py",
        language="python",
        symbol_name="AuthenticationMiddleware",
        symbol_type="class",
        start_line=20,
        end_line=52,
        content="class AuthenticationMiddleware: return 401",
        content_hash="hash1",
    )
    c2 = CodeChunk(
        id="c2",
        repository_id="repo1",
        file_id="f2",
        file_path="backend/routes/items.py",
        language="python",
        symbol_name="list_items",
        symbol_type="function",
        start_line=1,
        end_line=10,
        content="def list_items(): return []",
        content_hash="hash2",
    )

    cand1 = RetrievedCandidate(chunk=c1, hybrid_score=0.8)
    cand2 = RetrievedCandidate(chunk=c2, hybrid_score=0.4)

    reranked = reranker_service.rerank("Why does authentication return 401?", [cand2, cand1], top_k=2)
    # Cand 1 should be ranked #1 because it matches 'auth', '401', and 'AuthenticationMiddleware'
    assert reranked[0].chunk.file_path == "backend/auth/middleware.py"

    # Context Builder test
    ctx = context_builder.build_context("demo-repo", "Why does authentication return 401?", reranked)
    assert len(ctx.citations) == 2
    assert ctx.citations[0].file_path == "backend/auth/middleware.py"
    assert ctx.citations[0].start_line == 20
    assert ctx.citations[0].end_line == 52
    assert "backend/auth/middleware.py" in ctx.formatted_prompt
