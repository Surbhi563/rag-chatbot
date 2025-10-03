# Render deployment configuration for Ollama
# This file tells Render how to deploy Ollama

# Build command (Render will use the Dockerfile)
# Start command: ollama serve

# Environment variables needed:
# - PORT (automatically set by Render)
# - OLLAMA_HOST=0.0.0.0:$PORT

# Deployment Steps:
# 1. Create new Web Service on Render
# 2. Connect GitHub repository
# 3. Set Root Directory to: ollama
# 4. Set Dockerfile Path to: Dockerfile.render (or Dockerfile.simple if the first doesn't work)
# 5. Set Start Command to: ollama serve
# 6. Deploy!

# After deployment:
# 1. Go to your Ollama service console
# 2. Run: ollama pull llama3.2:3b
# 3. Update backend LLM_BASE_URL to your Ollama service URL

# If you get "unknown command ollama" error:
# - Try using Dockerfile.simple instead
# - Or use the official Ollama Docker image with correct entrypoint
