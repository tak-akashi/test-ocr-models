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
    if [ ! -f "/app/.env" ] && [ -z "$UPSTAGE_API_KEY" ] && [ -z "$AZURE_DOCUMENT_INTELLIGENCE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
        warn "No API keys detected. Some processing services may not work."
        warn "Mount your .env file or set environment variables for:"
        warn "  - UPSTAGE_API_KEY (Upstage Document Parse)"
        warn "  - AZURE_DOCUMENT_INTELLIGENCE_API_KEY (Azure)"
        warn "  - AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT (Azure)"
        warn "  - GEMINI_API_KEY (Google Gemini)"
        warn "  - ANTHROPIC_API_KEY (Claude)"
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
        "layout")
            log "Starting layout analysis..."
            shift
            exec layout "$@"
            ;;
        "ocr")
            log "Starting OCR-only processing..."
            shift
            exec ocr "$@"
            ;;
        "preprocess"|"preprocessing")
            log "Starting preprocessing utilities..."
            shift
            exec preprocess "$@"
            ;;
        "models")
            log "Starting legacy model runner..."
            shift
            exec python -m src.run_models "$@"
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
            # If command starts with python, uv, jupyter, layout, ocr, or preprocess, execute directly
            if [[ "$1" =~ ^(python|uv|jupyter|layout|ocr|preprocess) ]]; then
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
=============================

USAGE:
    docker run [OPTIONS] document-processor [COMMAND] [ARGS...]

COMMANDS:
    layout [ARGS]        Run layout analysis models
    ocr [ARGS]           Run OCR-only models
    preprocess [ARGS]    Run PDF preprocessing utilities
    models [ARGS]        Run legacy model runner (backward compatibility)
    jupyter              Start Jupyter Lab server
    bash                 Start interactive bash shell
    help                 Show this help message

SUPPORTED MODELS:
    Layout mode:  upstage, azure, yomitoku, gemini, claude, qwen
    OCR mode:     upstage, azure, yomitoku, gemini, claude, qwen (with -ocr suffix)
    Use 'all' to run all models

EXAMPLES:
    # Run layout analysis with all models
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor layout --models all

    # Run layout analysis with specific models
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor layout --models upstage azure

    # Run OCR-only with specific models
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor ocr --models upstage gemini

    # Run Qwen with GPU optimization
    docker run --rm --gpus all -v ./data:/app/data -v ./output:/app/output document-processor-gpu layout --models qwen --optimize

    # Preprocessing - extract specific pages
    docker run --rm -v ./data:/app/data document-processor preprocess extract input.pdf --pages 1 2 3

    # Preprocessing - split PDF into individual pages
    docker run --rm -v ./data:/app/data document-processor preprocess split input.pdf

    # Preprocessing - convert PDF to images
    docker run --rm -v ./data:/app/data document-processor preprocess images input.pdf --dpi-scale 2.0

    # Start Jupyter Lab
    docker run --rm -p 8888:8888 -v ./notebook:/app/notebook document-processor jupyter

    # Interactive shell
    docker run --rm -it -v ./:/app document-processor bash

    # Legacy: Run specific model variants directly
    docker run --rm -v ./data:/app/data -v ./output:/app/output document-processor models --models upstage upstage-ocr azure-ocr

VOLUMES:
    /app/data        - Input PDF/image files (read-only recommended)
    /app/output      - Processing results and outputs
    /app/notebook    - Jupyter notebooks
    /app/.cache      - Model cache directory (Hugging Face models)

ENVIRONMENT VARIABLES:
    UPSTAGE_API_KEY                      - Upstage Document Parse API key
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY  - Azure Document Intelligence API key
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT - Azure Document Intelligence endpoint
    GEMINI_API_KEY                       - Google Gemini API key
    ANTHROPIC_API_KEY                    - Anthropic Claude API key

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