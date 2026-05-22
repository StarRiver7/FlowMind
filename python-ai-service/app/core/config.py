from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    app_name: str = "ai-agent-python-service"
    env: str = "dev"
    debug: bool = False

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    default_llm_provider: str = "openai"

    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024

    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "knowledge_chunks"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "123456"
    mysql_database: str = "enterprise_ai"
    mysql_readonly_url: str = ""
    mysql_write_url: str = ""

    java_service_url: str = "http://localhost:8080"
    java_service_api_key: str = "dev-api-key"

    agent_max_iterations: int = 10
    agent_timeout_seconds: int = 60
    conversation_window: int = 10
    tool_timeout_seconds: int = 30

    chunk_size: int = 512
    chunk_overlap: int = 64
    rag_top_k: int = 5
    rag_score_threshold: float = 0.5

    rate_limit_per_minute: int = 20
    rate_limit_tokens_per_day: int = 100000

    cors_origins: list[str] = ["*"]


settings = Settings()

# 动态构建数据库URL
if not settings.mysql_write_url:
    settings.mysql_write_url = (
        f"mysql+pymysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        "?charset=utf8mb4"
    )
if not settings.mysql_readonly_url:
    settings.mysql_readonly_url = settings.mysql_write_url
