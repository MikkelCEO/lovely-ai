#!/bin/bash

cd /workspace/Phone

apt-get update && apt-get install -y curl zstd

# Install Ollama if missing
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

git pull

pip install -r phone_requirements.txt

# Pull model if missing
ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# Start server with auto-reload
python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload