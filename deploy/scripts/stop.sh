#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Enterprise AI Agent Platform - Stopping Services ==="
docker compose -f "$PROJECT_ROOT/deploy/docker/docker-compose.yml" down
echo "=== All services stopped ==="
