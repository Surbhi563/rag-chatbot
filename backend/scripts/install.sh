#!/bin/bash

# APAC Atlas Taxonomy Service - Install Dependencies Script
# This script installs all required dependencies using uv

set -e  # Exit on any error

echo "🚀 Installing dependencies for APAC Atlas Taxonomy Service..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or"
    echo "   pip install uv"
    exit 1
fi

echo "✅ uv is installed"

# Install dependencies
echo "📦 Installing dependencies with uv..."
uv sync

echo "✅ Dependencies installed successfully!"
echo ""
echo "🎉 Installation complete! You can now:"
echo "   - Start server: ./scripts/start.sh"
echo "   - Or use make commands: make run"
