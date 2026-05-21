#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Enterprise AI Agent Platform - Build ==="

echo "[1/2] Building Java service..."
cd "$PROJECT_ROOT/java-service"
mvn clean package -DskipTests

echo "[2/2] Building Python AI service Docker image..."
cd "$PROJECT_ROOT/python-ai-service"
docker build -t ai-agent-python-service:latest .

echo "=== Build complete ==="
