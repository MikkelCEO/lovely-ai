#!/bin/bash

cd /workspace/Phone || exit 1

apt-get update && apt-get install -y curl zstd

# Install Ollama if missing
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Install cloudflared if missing
if ! command -v cloudflared &> /dev/null; then
  curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
  chmod +x /usr/local/bin/cloudflared
fi

# Start Ollama
ollama serve > /dev/null 2>&1 &

# Wait for Ollama
sleep 5

git pull

pip install -r phone_requirements.txt

# Ensure model exists
ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# Start API in background
python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload > /workspace/Phone/uvicorn.log 2>&1 &

# Wait for API to come up
sleep 5

# Start Cloudflare tunnel in foreground so container stays alive
cloudflared tunnel run ai