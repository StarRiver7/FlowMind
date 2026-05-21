FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry==2.1.2 && \
    poetry config virtualenvs.create false

# 安装依赖（poetry.lock不存在时自动生成）
RUN if [ -f poetry.lock ]; then \
        poetry install --no-root --without dev --no-interaction --no-ansi; \
    else \
        poetry install --no-root --without dev --no-interaction --no-ansi 2>/dev/null || \
        pip install fastapi uvicorn pydantic pydantic-settings langchain langchain-openai redis httpx; \
    fi

FROM python:3.11-slim

RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid 1001 appuser && \
    apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ai/health || exit 1

ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
