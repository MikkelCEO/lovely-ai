#!/bin/bash

cd /workspace/Phone

apt-get update && apt-get install -y curl zstd

# Install Ollama if missing
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama
ollama serve > /dev/null 2>&1 &

# Wait for Ollama to be ready
sleep 5

git pull

pip install -r phone_requirements.txt

# Ensure model exists
ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# Start API
python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload