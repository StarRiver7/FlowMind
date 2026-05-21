import pytest


class TestHealthAPI:
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client):
        response = await async_client.get("/ai/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ai-agent-python-service"

    @pytest.mark.asyncio
    async def test_health_without_api_key(self):
        from httpx import AsyncClient, ASGITransport
        from src.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ai/health")
            assert response.status_code == 401  # No API key
