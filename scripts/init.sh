#!/bin/bash
set -euo pipefail

echo "=== Enterprise AI Agent Platform - Project Initialization ==="

# Initialize Java service
echo "[1/2] Initializing Java service..."
cd java-service
mvn clean compile

# Initialize Python AI service
echo "[2/2] Initializing Python AI service..."
cd ../python-ai-service
pip install poetry
poetry install

echo "=== Project initialization complete ==="
