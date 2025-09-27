#!/bin/bash
set -e

# Docker entrypoint script for document processing project
# Handles permissions, initialization, and command routing

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

# Fix permissions for mounted volumes
fix_permissions() {
    log "Fixing permissions for mounted volumes..."

    # Get host user/group IDs from mounted directory ownership
    if [ -d "/app/data" ]; then
        HOST_UID=$(stat -c "%u" /app/data)
        HOST_GID=$(stat -c "%g" /app/data)
    else
        HOST_UID=1000
        HOST_GID=1000
    fi

    log "Detected host UID: $HOST_UID, GID: $HOST_GID"

    # Create directories if they don't exist and fix ownership
    for dir in "/app/data" "/app/output" "/app/notebook" "/app/.cache"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
        fi

        # Change ownership to host user for write access
        if [ -w "$dir" ] || [ "$EUID" -eq 0 ]; then
            chown -R $HOST_UID:$HOST_GID "$dir" 2>/dev/null || true
            chmod -R 775 "$dir" 2>/dev/null || true
        fi
    done

    # Update appuser UID/GID if running as root
    if [ "$EUID" -eq 0 ]; then
        # Check if appuser exists and update IDs
        if id appuser >/dev/null 2>&1; then
            usermod -u $HOST_UID appuser 2>/dev/null || true
            groupmod -g $HOST_GID appuser 2>/dev/null || true
        else
            # Create appuser with host IDs
            groupadd -g $HOST_GID appuser 2>/dev/null || true
            useradd -u $HOST_UID -g $HOST_GID -d /home/appuser -s /bin/bash appuser 2>/dev/null || true
        fi

        # Ensure appuser owns home directory
        mkdir -p /home/appuser
        chown -R $HOST_UID:$HOST_GID /home/appuser 2>/dev/null || true
    fi

    success "Permissions fixed successfully"
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

    # Set Hugging Face environment variables to avoid XetHub DNS issues
    log "Configuring Hugging Face settings..."
    export HF_HUB_ETAG_TIMEOUT=${HF_HUB_ETAG_TIMEOUT:-60}
    export HF_HUB_DOWNLOAD_TIMEOUT=${HF_HUB_DOWNLOAD_TIMEOUT:-300}
    export HF_HUB_DISABLE_SYMLINKS_WARNING=${HF_HUB_DISABLE_SYMLINKS_WARNING:-1}
    export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=${HF_HUB_DISABLE_EXPERIMENTAL_WARNING:-1}
    export HF_HUB_DISABLE_TELEMETRY=${HF_HUB_DISABLE_TELEMETRY:-1}
    # Disable XetHub by not using experimental features
    export HF_HUB_ENABLE_HF_TRANSFER=${HF_HUB_ENABLE_HF_TRANSFER:-0}
    export HF_ENABLE_EXPERIMENTAL_FEATURES=${HF_ENABLE_EXPERIMENTAL_FEATURES:-0}

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

    # Fix permissions first (must be done as root)
    if [ "$EUID" -eq 0 ]; then
        fix_permissions

        # Initialize environment
        init_directories
        check_environment
        check_gpu

        # Switch to appuser using gosu for remaining operations
        if command -v gosu >/dev/null 2>&1; then
            # Handle commands as appuser
            if [ $# -eq 0 ]; then
                log "No command provided, starting interactive shell as appuser"
                exec gosu appuser bash
            else
                log "Executing command as appuser: $*"
                exec gosu appuser "$0" "--as-user" "$@"
            fi
        else
            error "gosu not found, cannot switch user safely"
            exit 1
        fi
    elif [ "$1" = "--as-user" ]; then
        # Running as appuser after gosu switch
        shift
        # Re-run environment checks as user
        check_environment
        check_gpu

        # Handle commands
        if [ $# -eq 0 ]; then
            log "Starting interactive shell"
            handle_command "bash"
        else
            handle_command "$@"
        fi
    else
        # Running as non-root user directly
        log "Running as non-root user (UID: $(id -u))"
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
    fi
}

# Execute main function with all arguments
main "$@"