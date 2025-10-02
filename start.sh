#!/bin/bash

# RAG Chatbot Startup Script

set -e

echo "🚀 Starting RAG Chatbot..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "📦 Using Docker Compose..."
    
    # Create data directory
    mkdir -p data
    
    # Start services
    docker-compose up --build
else
    echo "🔧 Using local development setup..."
    
    # Check if required tools are installed
    if ! command -v uv &> /dev/null; then
        echo "❌ uv is not installed. Please install it first:"
        echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo "❌ npm is not installed. Please install Node.js first."
        exit 1
    fi
    
    # Start backend
    echo "🔧 Starting backend..."
    cd backend
    if [ ! -f .env ]; then
        cp env.example .env
        echo "📝 Created .env file. Please edit it with your configuration."
    fi
    
    # Install dependencies and start backend in background
    uv sync --dev
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    sleep 5
    
    # Start frontend
    echo "🎨 Starting frontend..."
    cd ../frontend
    npm install
    npm start &
    FRONTEND_PID=$!
    
    echo "✅ RAG Chatbot is running!"
    echo "   Backend: http://localhost:8080"
    echo "   Frontend: http://localhost:3000"
    echo "   API Docs: http://localhost:8080/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for user to stop
    wait $BACKEND_PID $FRONTEND_PID
fi
