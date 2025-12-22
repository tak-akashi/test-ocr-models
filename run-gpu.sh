#!/bin/bash
# GPU-enabled document processor runner
# Usage: ./run-gpu.sh ocr --models yomitoku
#        ./run-gpu.sh layout --models qwen --optimize

set -e

# Check if GPU is available
if ! nvidia-smi &> /dev/null; then
    echo "WARNING: nvidia-smi not found. GPU may not be available."
    echo "Falling back to CPU mode..."
    docker compose run --rm document-processor "$@"
else
    echo "GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
    docker compose --profile gpu run --rm document-processor-gpu "$@"
fi
