#!/bin/bash
# Document Processing Docker Helper Script for Linux/macOS
# =========================================================
#
# Usage:
#   ./docker-run.sh layout [--models all] [--gpu] [--optimize]
#   ./docker-run.sh ocr [--models upstage azure]
#   ./docker-run.sh jupyter
#   ./docker-run.sh shell
#   ./docker-run.sh build [--gpu]
#   ./docker-run.sh help

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_ROOT"

# Default values
GPU=false
OPTIMIZE=false
MODELS="all"
SAMPLES=""
INPUT=""

# Parse global options
parse_options() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --gpu)
                GPU=true
                shift
                ;;
            --optimize)
                OPTIMIZE=true
                shift
                ;;
            --models)
                MODELS="$2"
                shift 2
                ;;
            --n-samples)
                SAMPLES="$2"
                shift 2
                ;;
            --input)
                INPUT="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    REMAINING_ARGS=("$@")
}

# Check Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Docker is not running. Please start Docker.${NC}"
        exit 1
    fi
}

# Ensure required directories exist
ensure_dirs() {
    mkdir -p data output .cache
}

# Get service name based on GPU flag
get_service() {
    if [ "$GPU" = true ]; then
        echo "document-processor-gpu"
    else
        echo "document-processor"
    fi
}

# Get compose profile
get_profile() {
    if [ "$GPU" = true ]; then
        echo "--profile gpu"
    else
        echo ""
    fi
}

# Build extra args
build_extra_args() {
    local args=""
    if [ "$OPTIMIZE" = true ]; then
        args="$args --optimize"
    fi
    if [ -n "$SAMPLES" ]; then
        args="$args --n-samples $SAMPLES"
    fi
    if [ -n "$INPUT" ]; then
        args="$args --input $INPUT"
    fi
    echo "$args"
}

# Commands
cmd_layout() {
    shift  # Remove 'layout' from args
    parse_options "$@"

    local service=$(get_service)
    local profile=$(get_profile)
    local extra=$(build_extra_args)

    echo -e "${CYAN}Running layout analysis...${NC}"
    local cmd="docker compose $profile run --rm $service layout --models $MODELS $extra"
    echo -e "${YELLOW}Command: $cmd${NC}"
    eval $cmd
}

cmd_ocr() {
    shift  # Remove 'ocr' from args
    parse_options "$@"

    local service=$(get_service)
    local profile=$(get_profile)
    local extra=$(build_extra_args)

    echo -e "${CYAN}Running OCR processing...${NC}"
    local cmd="docker compose $profile run --rm $service ocr --models $MODELS $extra"
    echo -e "${YELLOW}Command: $cmd${NC}"
    eval $cmd
}

cmd_preprocess() {
    shift  # Remove 'preprocess' from args

    echo -e "${CYAN}Running preprocessing...${NC}"
    docker compose run --rm document-processor preprocess "$@"
}

cmd_jupyter() {
    echo -e "${CYAN}Starting Jupyter Lab...${NC}"
    echo -e "${YELLOW}Access at: http://localhost:8890${NC}"
    docker compose --profile jupyter up jupyter
}

cmd_shell() {
    parse_options "${@:2}"

    local service=$(get_service)
    local profile=$(get_profile)

    echo -e "${CYAN}Starting interactive shell...${NC}"
    docker compose $profile run --rm $service bash
}

cmd_build() {
    parse_options "${@:2}"

    echo -e "${CYAN}Building Docker images...${NC}"
    if [ "$GPU" = true ]; then
        docker compose --profile gpu build
    else
        docker compose build
    fi
}

cmd_help() {
    cat << 'EOF'

Document Processing Docker Helper
==================================

USAGE:
    ./docker-run.sh <command> [options]

COMMANDS:
    layout      Run layout analysis models
    ocr         Run OCR-only processing
    preprocess  Run PDF preprocessing utilities
    jupyter     Start Jupyter Lab server
    shell       Start interactive bash shell
    build       Build Docker images
    help        Show this help message

OPTIONS:
    --models <list>     Comma-separated models (upstage,azure,yomitoku,gemini,claude,qwen or 'all')
    --gpu               Use GPU-enabled container
    --optimize          Enable GPU optimization for Qwen model
    --n-samples <n>     Limit processing to first N files
    --input <path>      Specify input file or directory

EXAMPLES:
    # Run all layout models
    ./docker-run.sh layout --models all

    # Run specific OCR models
    ./docker-run.sh ocr --models upstage,azure

    # Run Qwen with GPU
    ./docker-run.sh layout --models qwen --gpu --optimize

    # Process first 5 files only
    ./docker-run.sh layout --models upstage --n-samples 5

    # Start Jupyter Lab
    ./docker-run.sh jupyter

    # Interactive shell
    ./docker-run.sh shell

    # Interactive shell with GPU
    ./docker-run.sh shell --gpu

REQUIREMENTS:
    - Docker and Docker Compose
    - .env file with API keys
    - For GPU: NVIDIA GPU with Docker GPU support

EOF
}

# Main
main() {
    check_docker
    ensure_dirs

    local command="${1:-help}"

    case "$command" in
        layout)
            cmd_layout "$@"
            ;;
        ocr)
            cmd_ocr "$@"
            ;;
        preprocess)
            cmd_preprocess "$@"
            ;;
        jupyter)
            cmd_jupyter
            ;;
        shell)
            cmd_shell "$@"
            ;;
        build)
            cmd_build "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
