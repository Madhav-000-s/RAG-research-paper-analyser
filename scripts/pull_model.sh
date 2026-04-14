#!/bin/bash
# Pull the Ollama model after the container is running
echo "Pulling Ollama model..."
docker compose exec ollama ollama pull llama3.1:8b
echo "Model pull complete!"
