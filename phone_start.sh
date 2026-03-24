#!/bin/bash

cd /volume1/Projects/ai-chat/Phone

# Pull latest code
git pull

# Install dependencies (NAS-safe)
pip install -r phone_requirements.txt --break-system-packages

