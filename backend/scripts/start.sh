#!/bin/bash

# APAC Atlas Taxonomy Service - Start Server Script
# This script starts the FastAPI development server

set -e  # Exit on any error

echo "🚀 Starting APAC Atlas Taxonomy Service..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or"
    echo "   pip install uv"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ]; then
    echo "⚠️  Dependencies not installed. Installing them first..."
    ./scripts/install.sh
fi

echo "✅ Dependencies are ready"

# Get configuration
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8080"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "🌐 Starting server on http://$HOST:$PORT"
echo "📚 API Documentation: http://$HOST:$PORT/docs"
echo "🔍 Health Check: http://$HOST:$PORT/health"
echo "🎯 Taxonomy Endpoint: http://$HOST:$PORT/v1/taxonomy/generate"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uv run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload --log-level "$LOG_LEVEL"
