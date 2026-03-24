#!/bin/bash

cd /workspace/Phone

apt-get update && apt-get install -y curl zstd

# Install Ollama if missing
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

git pull

pip install -r phone_requirements.txt

# AUTO RELOAD ON FILE CHANGE
python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload
