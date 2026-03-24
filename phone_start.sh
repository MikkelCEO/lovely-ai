#!/bin/bash

cd /workspace/Phone

apt-get update && apt-get install -y curl zstd

git pull

pip install -r phone_requirements.txt

python -m uvicorn phone_main:app --host 0.0.0.0 --port 8000
