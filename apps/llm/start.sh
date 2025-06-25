#!/bin/bash
set -e

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Download spacy model if needed
# python -c "import spacy; spacy.cli.download('en_core_web_sm')" 2>/dev/null || true

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload 