#!/bin/bash

cd /volume1/Projects/ai-chat/Phone

# Pull latest code
git pull

# Install dependencies (NAS-safe)
pip install -r phone_requirements.txt --break-system-packages

# Start auto-update loop
nohup bash -c '
cd /volume1/Projects/ai-chat/Phone
while true; do
  git fetch
  LOCAL=$(git rev-parse HEAD)
  REMOTE=$(git rev-parse origin/main)

  if [ "$LOCAL" != "$REMOTE" ]; then
    echo "Updating code..."
    git pull
  fi

  sleep 2
done
' > gitpull.log 2>&1 &
