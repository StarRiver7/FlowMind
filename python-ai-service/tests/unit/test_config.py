import pytest
from src.config import Settings


class TestConfig:
    def test_default_values(self):
        settings = Settings()
        assert settings.app_name == "ai-agent-python-service"
        assert settings.env == "dev"
        assert settings.agent_max_iterations == 10
        assert settings.chunk_size == 512
        assert settings.chunk_overlap == 64
        assert settings.rag_top_k == 5
        assert settings.rag_score_threshold == 0.5

    def test_mysql_write_url_format(self):
        settings = Settings()
        settings.mysql_host = "testhost"
        settings.mysql_port = 3307
        settings.mysql_user = "testuser"
        settings.mysql_password = "testpass"
        settings.mysql_database = "testdb"

        url = f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}?charset=utf8mb4"
        assert "testhost" in url
        assert "testdb" in url

    def test_cors_origins_default(self):
        settings = Settings()
        assert "*" in settings.cors_origins
