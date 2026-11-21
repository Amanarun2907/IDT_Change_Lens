import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ChangeLens" in data["service"]

@pytest.mark.asyncio
async def test_settings_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/settings")
        assert response.status_code == 200
        data = response.json()
        assert "available_providers" in data
        assert "gemini" in data["available_providers"]

@pytest.mark.asyncio
async def test_manual_analysis_raw_diff_submission():
    raw_diff = "--- a/math.py\n+++ b/math.py\n@@ -1,2 +1,3 @@\n-def add(a, b): return a\n+def add(a, b): return a + b"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/analysis/manual", json={
            "raw_diff": raw_diff,
            "language": "python",
            "filename": "math.py"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "queued"
