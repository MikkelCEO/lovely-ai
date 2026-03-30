#!/bin/bash

cd /workspace/Phone || exit 1

echo "=== STARTING PHONE AI STACK ==="

apt-get update && apt-get install -y curl zstd

# =========================================
# SETUP SSH ACCESS (RUNPOD LOGIN + NAS COMPAT)
# =========================================

mkdir -p /root/.ssh

cp /workspace/Phone/ssh/id_ed25519 /root/.ssh/id_ed25519
chmod 600 /root/.ssh/id_ed25519

cat /workspace/Phone/ssh/id_ed25519.pub >> /root/.ssh/authorized_keys

chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

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

sleep 5

# =========================================
# UPDATE PROJECT
# =========================================

git pull

pip install -r phone_requirements.txt

pip install -r phone_requirements.txt
pip install "uvicorn[standard]"

ollama list | grep -q "qwen2.5:3b" || ollama pull qwen2.5:3b

# =========================================
# RUNTIME CONFIG (LOCAL ONLY)
# =========================================

CONFIG_FILE_LOCAL="/workspace/Phone/pod_config.txt"

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

# =========================================
# START API (FIRST)
# =========================================

python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload &

# Wait for API to be ready
sleep 5

# =========================================
# START CLOUDFLARE TUNNEL (LAST)
# =========================================

/workspace/cloudflared tunnel run ai-temp