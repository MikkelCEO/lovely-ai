#!/bin/bash

FILE="/volume1/Projects/ai-chat/Lovely AI/main.py"
URL="https://w21vom80cinkwl-8000.proxy.runpod.net/upload"

echo "Watching $FILE..."

while inotifywait -e close_write "$FILE"; do
  echo "File changed, uploading..."
  curl -X POST -F "file=@$FILE" $URL
  echo "Uploaded!"
done