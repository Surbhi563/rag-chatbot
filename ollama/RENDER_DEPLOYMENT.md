# Render deployment configuration for Ollama
# This file tells Render how to deploy Ollama

# Build command (Render will use the Dockerfile)
# Start command: ollama serve

# Environment variables needed:
# - PORT (automatically set by Render)
# - OLLAMA_HOST=0.0.0.0:$PORT

# After deployment:
# 1. Go to your Ollama service console
# 2. Run: ollama pull llama3.2:3b
# 3. Update backend LLM_BASE_URL to your Ollama service URL
