#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Enterprise AI Agent Platform - Starting Services ==="

# Start infrastructure
echo "[1/3] Starting infrastructure (MySQL, Redis, Kafka)..."
docker compose -f "$PROJECT_ROOT/deploy/docker/docker-compose.yml" up -d mysql redis kafka

# Wait for infrastructure readiness
echo "Waiting for infrastructure to be ready..."
sleep 15

# Build and start services
echo "[2/3] Building and starting Java service..."
docker compose -f "$PROJECT_ROOT/deploy/docker/docker-compose.yml" up -d --build java-service

echo "[3/3] Building and starting Python AI service..."
docker compose -f "$PROJECT_ROOT/deploy/docker/docker-compose.yml" up -d --build python-ai-service

echo "=== All services started ==="
echo "Java Service:  http://localhost:8080"
echo "Python AI Service: http://localhost:8000"
echo "Actuator Health: http://localhost:8080/actuator/health"
