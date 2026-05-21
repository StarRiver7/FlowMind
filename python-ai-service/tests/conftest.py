import sys
import os
import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


@pytest.fixture
def test_settings():
    from src.config import settings
    settings.debug = True
    settings.env = "test"
    settings.redis_host = "localhost"
    settings.redis_port = 6379
    settings.mysql_host = "localhost"
    settings.mysql_port = 3306
    return settings


@pytest.fixture
async def async_client():
    from src.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Bypass API key middleware for tests
        client.headers["X-Api-Key"] = "dev-api-key"
        yield client
