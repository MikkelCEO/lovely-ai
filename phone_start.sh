#!/bin/bash

cd /workspace/Phone || exit 1

echo "=== STARTING PHONE AI STACK ==="

apt-get update && apt-get install -y curl zstd

# Install Ollama if missing
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama
ollama serve > /dev/null 2>&1 &

# Wait for Ollama
sleep 5

# Pull latest code
git pull

# Install requirements
pip install -r phone_requirements.txt

# Ensure model exists
ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# =========================================
# RUNTIME CONFIG (AUTO GENERATED)
# =========================================

CONFIG_FILE="/workspace/Phone/runtime_config.env"

POD_ID=$(hostname)
PUBLIC_IP=$(curl -s ifconfig.me)
LOCAL_IP=$(hostname -I | awk '{print $1}')

cat > $CONFIG_FILE <<EOF
POD_ID=$POD_ID
PUBLIC_IP=$PUBLIC_IP
LOCAL_IP=$LOCAL_IP
START_TIME=$(date)
EOF

echo "Runtime config written:"
cat $CONFIG_FILE

# =========================================
# START API
# =========================================

python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload