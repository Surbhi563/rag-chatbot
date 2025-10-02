# Makefile for APAC Atlas Taxonomy Service

.PHONY: help install dev test lint format clean run docker-build docker-run

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install dependencies using uv
	uv sync

dev: ## Install development dependencies
	uv sync --dev

# Code quality
lint: ## Run linting
	uv run ruff check .
	uv run mypy app/

format: ## Format code
	uv run black app/
	uv run isort app/
	uv run ruff check --fix .

# Application
run: ## Run the application locally
	uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Docker
docker-build: ## Build Docker image
	docker build -t apac-atlas-taxo-svc:latest .

docker-run: ## Run Docker container
	docker run -p 8080:8080 apac-atlas-taxo-svc:latest

# Cleanup
clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
