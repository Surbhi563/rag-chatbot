#!/bin/bash

# APAC Atlas Taxonomy Service - Docker Script
# This script builds and runs the application using Docker

set -e  # Exit on any error

echo "🐳 Docker workflow for APAC Atlas Taxonomy Service..."

# Function to show usage
show_usage() {
    echo "Usage: $0 [build|run|dev|clean]"
    echo ""
    echo "Commands:"
    echo "  build  - Build the Docker image"
    echo "  run    - Run the Docker container"
    echo "  dev    - Build and run in development mode"
    echo "  clean  - Clean up Docker images and containers"
    echo ""
    echo "Examples:"
    echo "  $0 build    # Build the image"
    echo "  $0 run      # Run the container"
    echo "  $0 dev      # Build and run"
    echo "  $0 clean    # Clean up"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Parse command
case "${1:-dev}" in
    "build")
        echo "🔨 Building Docker image..."
        docker build -t apac-atlas-taxo-svc:latest .
        echo "✅ Docker image built successfully!"
        echo "   Image: apac-atlas-taxo-svc:latest"
        ;;
    
    "run")
        echo "🚀 Running Docker container..."
        docker run -p 8080:8080 apac-atlas-taxo-svc:latest
        ;;
    
    "dev")
        echo "🛠️  Building and running in development mode..."
        docker build -t apac-atlas-taxo-svc:latest .
        echo "✅ Image built. Starting container..."
        echo "🌐 Server will be available at http://localhost:8080"
        echo "📚 API Documentation: http://localhost:8080/docs"
        echo "Press Ctrl+C to stop the container"
        docker run -p 8080:8080 apac-atlas-taxo-svc:latest
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker stop $(docker ps -q --filter ancestor=apac-atlas-taxo-svc:latest) 2>/dev/null || true
        docker rm $(docker ps -aq --filter ancestor=apac-atlas-taxo-svc:latest) 2>/dev/null || true
        docker rmi apac-atlas-taxo-svc:latest 2>/dev/null || true
        echo "✅ Docker cleanup completed!"
        ;;
    
    *)
        show_usage
        exit 1
        ;;
esac
