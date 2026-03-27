#!/bin/bash

cd /workspace/Phone || exit 1

echo "=== STARTING PHONE AI STACK ==="

apt-get update && apt-get install -y curl zstd

# =========================================
# SETUP SSH (FOR NAS SYNC)
# =========================================

mkdir -p /root/.ssh

cp /workspace/Phone/ssh/id_ed25519 /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519

ssh-keyscan -H 100.101.170.120 >> /root/.ssh/known_hosts

# =========================================
# INSTALL OLLAMA IF MISSING
# =========================================

if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi

# =========================================
# START OLLAMA
# =========================================

ollama serve > /dev/null 2>&1 &

# Wait for Ollama
sleep 5

# =========================================
# UPDATE PROJECT
# =========================================

git pull

pip install -r phone_requirements.txt

# Ensure model exists
ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# =========================================
# RUNTIME CONFIG (AUTO GENERATED)
# =========================================

CONFIG_FILE_LOCAL="/workspace/Phone/pod_config.txt"
CONFIG_FILE_NAS="mikkel.ceo@100.101.170.120:/volume1/Projects/ai-chat/Phone/config.txt"

POD_ID=$(hostname)
PUBLIC_IP=$(curl -s ifconfig.me)
LOCAL_IP=$(hostname -I | awk '{print $1}')

cat > $CONFIG_FILE_LOCAL <<EOF
POD_ID=$POD_ID
PUBLIC_IP=$PUBLIC_IP
LOCAL_IP=$LOCAL_IP
START_TIME=$(date)
EOF

echo "Runtime config (local):"
cat $CONFIG_FILE_LOCAL

# Push to NAS via HTTP
curl -X POST https://config.a1online.partners/update-config --data-binary @$CONFIG_FILE_LOCAL

echo "Config pushed to NAS"

# =========================================
# START API
# =========================================

python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload