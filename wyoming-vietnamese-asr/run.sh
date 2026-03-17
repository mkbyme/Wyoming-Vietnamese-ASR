#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# Read options
EMBEDDING_MODEL=$(jq --raw-output '.embedding_model // "qwen3-embedding:4b"' $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' $CONFIG_PATH)

# Set log level
export RUST_LOG=${LOG_LEVEL}

echo "🧠 Starting Wyoming Vietnamese ASR"
echo "   Embedding model: ${EMBEDDING_MODEL}"
echo "   Log level: ${LOG_LEVEL}"

# Start Wyoming server
exec python3 /app/server/main.py
