#!/bin/bash

DIR="/volume1/Projects/ai-chat/Lovely AI"

cd "$DIR"

echo "Watching for changes..."

while true; do
  inotifywait -r -e modify,create,delete "$DIR"

  echo "Change detected → committing..."

  git add .
  git commit -m "auto update" || echo "No changes to commit"
  git push

  echo "Synced!"
done
