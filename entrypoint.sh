#!/bin/bash
set -e

# Container entrypoint script for document processing project
# Handles initialization, permissions, and command routing

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Initialize directories
init_directories() {
    log "Initializing application directories..."

    # Ensure required directories exist
    mkdir -p /app/data /app/output /app/notebook /app/.cache/huggingface

    # Check if data directory is empty and warn
    if [ -z "$(ls -A /app/data 2>/dev/null)" ]; then
        warn "Data directory is empty. Mount your PDF files to /app/data"
    fi

    success "Directory initialization completed"
}

# Check environment variables
check_environment() {
    log "Checking environment configuration..."

    # Check if .env file exists or environment variables are set
    if [ ! -f "/app/.env" ] && [ -z "$UPSTAGE_API_KEY" ] && [ -z "$AZURE_DOCUMENT_INTELLIGENCE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
        warn "No API keys detected. Some processing services may not work."
        warn "Mount your .env file or set environment variables for:"
        warn "  - UPSTAGE_API_KEY"
        warn "  - AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
        warn "  - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
        warn "  - GEMINI_API_KEY"
    fi

    # Check Python path
    if [ "$PYTHONPATH" != "/app" ]; then
        warn "PYTHONPATH not set to /app, setting it now"
        export PYTHONPATH=/app
    fi

    success "Environment check completed"
}

# Check GPU availability (if applicable)
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        log "GPU support detected"
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits || warn "Could not query GPU status"
    else
        log "No GPU support detected - running in CPU mode"
    fi
}

# Handle different command types
handle_command() {
    case "$1" in
        "baseline"|"run-baseline")
            log "Starting baseline document processing..."
            shift
            exec python -m src.run_baseline "$@"
            ;;
        "qwen"|"run-qwen")
            log "Starting Qwen model processing..."
            shift
            exec python -m src.run_qwen "$@"
            ;;
        "preprocessing"|"preprocess")
            log "Starting preprocessing utilities..."
            shift
            exec python -m src.run_preprocessing "$@"
            ;;
        "jupyter"|"jupyter-lab"|"lab")
            log "Starting Jupyter Lab..."
            exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''
            ;;
        "bash"|"sh"|"shell")
            log "Starting interactive shell..."
            exec bash
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            # If command starts with python, uv, or jupyter, execute directly
            if [[ "$1" =~ ^(python|uv|jupyter) ]]; then
                log "Executing command: $*"
                exec "$@"
            else
                log "Unknown command: $1"
                show_help
                exit 1
            fi
            ;;
    esac
}

# Show usage help
show_help() {
    cat << EOF
Document Processing Container

USAGE:
    docker run [OPTIONS] document-processor [COMMAND] [ARGS...]

COMMANDS:
    baseline [ARGS]       Run baseline models (Upstage, Azure, YOMITOKU, Gemini)
    qwen [ARGS]          Run Qwen VL models
    preprocessing [ARGS] Run PDF preprocessing utilities
    jupyter              Start Jupyter Lab server
    bash                 Start interactive bash shell
    help                 Show this help message

EXAMPLES:
    # Run baseline processing on all files in /app/data
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor baseline

    # Run Qwen models on specific file
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor qwen specific.pdf

    # Start Jupyter Lab
    docker run --rm -p 8888:8888 -v ./notebook:/app/notebook document-processor jupyter

    # Interactive shell
    docker run --rm -it -v ./:/app document-processor bash

    # Preprocessing - extract specific pages
    docker run --rm -v ./data:/app/data document-processor preprocessing extract input.pdf --pages 1 2 3

VOLUMES:
    /app/data        - Input PDF files (read-only recommended)
    /app/output      - Processing results and outputs
    /app/notebook    - Jupyter notebooks
    /app/.cache      - Model cache directory

ENVIRONMENT VARIABLES:
    UPSTAGE_API_KEY                      - Upstage Document Parse API key
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY  - Azure Document Intelligence API key
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT - Azure Document Intelligence endpoint
    GEMINI_API_KEY                       - Google Gemini API key

For more information, see the project documentation.
EOF
}

# Main execution
main() {
    log "Starting document processing container..."

    # Initialize environment
    init_directories
    check_environment
    check_gpu

    # Handle commands
    if [ $# -eq 0 ]; then
        log "No command provided, starting interactive shell"
        handle_command "bash"
    else
        handle_command "$@"
    fi
}

# Execute main function with all arguments
main "$@"