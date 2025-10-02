#!/bin/bash

# APAC Atlas Taxonomy Service - Uninstall Script
# This script removes all dependencies, virtual environment, and build artifacts

set -e  # Exit on any error

echo "🧹 Uninstalling APAC Atlas Taxonomy Service..."

# Function to confirm action
confirm() {
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Uninstall cancelled."
        exit 1
    fi
}

# Show what will be removed
echo "This will remove:"
echo "  - Virtual environment (.venv/)"
echo "  - Python cache files (__pycache__/)"
echo "  - Build artifacts (dist/, build/)"
echo "  - MyPy cache (.mypy_cache/)"
echo "  - UV lock file (uv.lock)"
echo "  - Docker images (apac-atlas-taxo-svc:latest)"
echo ""

# Ask for confirmation
confirm

echo "🗑️  Removing virtual environment..."
if [ -d ".venv" ]; then
    rm -rf .venv
    echo "✅ Virtual environment removed"
else
    echo "ℹ️  No virtual environment found"
fi

echo "🗑️  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo "✅ Python cache files removed"

echo "🗑️  Removing build artifacts..."
rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true
echo "✅ Build artifacts removed"

echo "🗑️  Removing cache artifacts..."
rm -rf .mypy_cache/ 2>/dev/null || true
echo "✅ Cache artifacts removed"

echo "🗑️  Removing lock file..."
rm -f uv.lock 2>/dev/null || true
echo "✅ Lock file removed"

echo "🗑️  Removing Docker images..."
if command -v docker &> /dev/null; then
    # Stop and remove containers
    docker stop $(docker ps -q --filter ancestor=apac-atlas-taxo-svc:latest) 2>/dev/null || true
    docker rm $(docker ps -aq --filter ancestor=apac-atlas-taxo-svc:latest) 2>/dev/null || true
    
    # Remove images
    docker rmi apac-atlas-taxo-svc:latest 2>/dev/null || true
    echo "✅ Docker images removed"
else
    echo "ℹ️  Docker not found, skipping Docker cleanup"
fi

echo "🗑️  Removing temporary files..."
rm -f *.tmp *.temp 2>/dev/null || true
echo "✅ Temporary files removed"

echo ""
echo "✅ Uninstall completed successfully!"
echo ""
echo "🎯 To start fresh:"
echo "   ./scripts/install.sh    # Install dependencies"
echo "   ./scripts/dev.sh        # Complete development workflow"
echo ""
echo "📝 Note: Source code and configuration files were preserved."
