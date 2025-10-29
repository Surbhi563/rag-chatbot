#!/bin/bash

# Start Ollama server in background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
sleep 5

# Check if Ollama is responding
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    echo "Waiting for Ollama... ($i/30)"
    sleep 2
done

# Pull the model if not already available
echo "Checking for model llama3.2:3b..."
MODEL_EXISTS=$(ollama list | grep -c "llama3.2:3b" || echo "0")

if [ "$MODEL_EXISTS" = "0" ]; then
    echo "Model not found. Pulling llama3.2:3b..."
    ollama pull llama3.2:3b
    echo "Model pulled successfully!"
else
    echo "Model already exists!"
fi

# Keep Ollama running
echo "Ollama is running with model llama3.2:3b"
wait $OLLAMA_PID

