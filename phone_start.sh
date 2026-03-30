#!/bin/bash

cd /workspace/Phone || exit 1

echo ""
echo "=== STARTING PHONE AI STACK ==="
echo ""

# =========================================
# STATUS HELPERS
# =========================================
ok()   { echo "🟢 $1"; }
warn() { echo "🟡 $1"; }
fail() { echo "🔴 $1"; }

wait_for_service() {
  URL=$1
  NAME=$2
  for i in {1..10}; do
    if curl -s "$URL" > /dev/null; then
      ok "$NAME"
      return 0
    fi
    sleep 1
  done
  fail "$NAME"
  return 1
}

# =========================================
# BASE INSTALL (SILENT)
# =========================================
apt-get update -qq > /dev/null 2>&1
apt-get install -y curl zstd -qq > /dev/null 2>&1

# =========================================
# GPU CHECK
# =========================================
if command -v nvidia-smi &> /dev/null; then
  GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)
  ok "GPU detected ($GPU_NAME)"
else
  warn "No GPU detected (running CPU mode)"
fi

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
wait_for_service "http://localhost:11434" "Ollama running"

# =========================================
# UPDATE PROJECT + INSTALL
# =========================================
git pull > /dev/null 2>&1

pip install -r phone_requirements.txt > /dev/null 2>&1
pip install "uvicorn[standard]" > /dev/null 2>&1

ok "Dependencies installed"

# =========================================
# ENSURE MODEL
# =========================================
MODEL="qwen2.5:1.5b"

if ollama list | grep -q "$MODEL"; then
  ok "Model already present ($MODEL)"
else
  warn "Downloading model ($MODEL)..."
  ollama pull $MODEL > /dev/null 2>&1
  ok "Model downloaded"
fi

# =========================================
# MODEL WARMUP (IMPORTANT)
# =========================================
curl -s http://localhost:11434/api/chat \
  -d '{"model":"qwen2.5:1.5b","messages":[{"role":"user","content":"hi"}]}' \
  > /dev/null 2>&1

ok "Model warmed up"

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
wait_for_service "http://localhost:8000" "FastAPI running (8000)"


# =========================================
# FINAL SUMMARY
# =========================================
echo ""
echo "=== SYSTEM READY ==="
echo "URL: https://ai.a1online.partners"
echo ""