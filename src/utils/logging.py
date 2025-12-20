"""Logging utilities with consistent timestamp format."""

import logging
import os
import sys
import warnings
from datetime import datetime

# ============================================================================
# Environment variables must be set BEFORE importing third-party libraries
# ============================================================================

# Suppress HuggingFace progress bars and warnings
os.environ["TQDM_DISABLE"] = "1"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_EXPERIMENTAL_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress ONNX Runtime warnings (including cpuid_info)
os.environ["ORT_LOG_LEVEL"] = "3"  # 3 = ERROR level

# ============================================================================
# Logging configuration
# ============================================================================

# Suppress third-party library logs
logging.getLogger("yomitoku").setLevel(logging.ERROR)
logging.getLogger("yomitoku.base").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("filelock").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)

# ============================================================================
# Warning filters
# ============================================================================

# Suppress Python warnings
warnings.filterwarnings("ignore", message=".*You are sending unauthenticated requests.*")
warnings.filterwarnings("ignore", message=".*unauthenticated.*")
warnings.filterwarnings("ignore", message=".*HF_TOKEN.*")
warnings.filterwarnings("ignore", module="huggingface_hub")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", category=FutureWarning)

# Try to disable huggingface_hub warnings programmatically
try:
    from huggingface_hub.utils import disable_progress_bars
    disable_progress_bars()
except ImportError:
    pass

try:
    import huggingface_hub
    huggingface_hub.logging.set_verbosity_error()
except (ImportError, AttributeError):
    pass


# ============================================================================
# ANSI Color codes (matching entrypoint.sh)
# ============================================================================

BLUE = "\033[0;34m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color


def _timestamp():
    """Get current timestamp in consistent format with color."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{BLUE}[{ts}]{NC}"


def log(message: str):
    """Print a log message with timestamp."""
    print(f"{_timestamp()} {message}")


def log_success(message: str):
    """Print a success message with timestamp."""
    print(f"{_timestamp()} {GREEN}SUCCESS:{NC} {message}")


def log_warning(message: str):
    """Print a warning message with timestamp."""
    print(f"{_timestamp()} {YELLOW}WARNING:{NC} {message}")


def log_error(message: str):
    """Print an error message with timestamp."""
    print(f"{_timestamp()} {RED}ERROR:{NC} {message}", file=sys.stderr)


def log_info(message: str):
    """Print an info message with timestamp (same as log)."""
    log(message)


def log_processing(filename: str, current: int, total: int):
    """Log file processing progress."""
    log(f"Processing {filename}... ({current}/{total})")


def log_model_start(model_name: str):
    """Log model processing start."""
    print(f"{_timestamp()}   Processing {model_name}...")


def log_model_complete(model_name: str, elapsed_time: float):
    """Log model processing completion."""
    print(f"{_timestamp()}   {GREEN}{model_name} completed in {elapsed_time:.2f} seconds{NC}")


def log_model_error(model_name: str, error: str):
    """Log model processing error."""
    print(f"{_timestamp()}   {RED}{model_name} failed: {error}{NC}", file=sys.stderr)


def log_file_complete(file_index: int):
    """Log file processing completion."""
    print(f"{_timestamp()}   File {file_index} completed\n")
