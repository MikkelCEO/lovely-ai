#!/bin/bash

cd /workspace/Phone || exit 1

echo ""
echo "=== STARTING PHONE AI STACK ==="
echo ""

# =========================================
# STATUS HELPERS
# =========================================
ok() { echo "🟢 $1"; }
fail() { echo "🔴 $1"; }

# =========================================
# BASE INSTALL (SILENT)
# =========================================
apt-get update -qq > /dev/null 2>&1
apt-get install -y curl zstd -qq > /dev/null 2>&1

# =========================================
# SSH SETUP
# =========================================
mkdir -p /root/.ssh

cp /workspace/Phone/ssh/id_ed25519 /root/.ssh/id_ed25519 2>/dev/null
chmod 600 /root/.ssh/id_ed25519

cat /workspace/Phone/ssh/id_ed25519.pub >> /root/.ssh/authorized_keys 2>/dev/null

chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

ssh-keyscan -H 100.101.170.120 >> /root/.ssh/known_hosts 2>/dev/null

ok "SSH ready"

# =========================================
# INSTALL OLLAMA
# =========================================
if ! command -v ollama &> /dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
fi

# =========================================
# START OLLAMA
# =========================================
ollama serve > /dev/null 2>&1 &

sleep 3

if curl -s http://localhost:11434 > /dev/null; then
  ok "Ollama running"
else
  fail "Ollama failed"
fi

# =========================================
# UPDATE PROJECT + INSTALL
# =========================================
git pull > /dev/null 2>&1

pip install -r phone_requirements.txt > /dev/null 2>&1
pip install "uvicorn[standard]" > /dev/null 2>&1

ok "Dependencies installed"

# =========================================
# ENSURE MODEL (UPDATED TO 1.5b)
# =========================================
ollama list | grep -q "qwen2.5:1.5b" || ollama pull qwen2.5:1.5b > /dev/null 2>&1

ok "Model ready (qwen2.5:1.5b)"

# =========================================
# RUNTIME CONFIG
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

ok "Runtime config written"

# =========================================
# START FASTAPI
# =========================================
python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000 --reload > /dev/null 2>&1 &

sleep 3

if curl -s http://localhost:8000 > /dev/null; then
  ok "FastAPI running (8000)"
else
  fail "FastAPI failed"
fi

# =========================================
# START CLOUDFLARE (LAST!)
# =========================================
/workspace/cloudflared tunnel run ai-temp > /dev/null 2>&1 &

sleep 5

if pgrep -f cloudflared > /dev/null; then
  ok "Cloudflare tunnel running"
else
  fail "Cloudflare failed"
fi

# =========================================
# FINAL STATUS
# =========================================
echo ""
echo "=== SYSTEM READY ==="
echo ""