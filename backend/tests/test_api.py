import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import init_db

@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "RepoPilot"

@pytest.mark.asyncio
async def test_repository_registration_and_indexing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register sample repo
        sample_path = os.path.join(os.getcwd(), "examples", "sample-repo")
        response = await ac.post("/api/repositories", json={"url": sample_path, "branch": "main"})
        assert response.status_code == 200
        repo_data = response.json()
        repo_id = repo_data["id"]
        assert repo_id is not None

        # Verify indexing status endpoint
        status_res = await ac.get(f"/api/repositories/{repo_id}/index-status")
        assert status_res.status_code == 200
        assert "status" in status_res.json()

        # Check repository listing
        list_res = await ac.get("/api/repositories")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1
