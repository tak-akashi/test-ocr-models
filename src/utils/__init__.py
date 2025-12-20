"""
Utility functions for document processing.

Modules:
    timing - Execution time measurement utilities
    file_utils - File I/O helpers (save_html, save_markdown)
    html_utils - HTML normalization utilities
    etl_extractor - ETL dataset extraction utilities
    logging - Logging utilities with consistent timestamp format
"""

from .logging import (
    log, log_success, log_warning, log_error, log_info,
    log_processing, log_model_start, log_model_complete,
    log_model_error, log_file_complete
)
from .timing import measure_time, save_timing_results, print_timing_summary
from .file_utils import save_html, save_markdown

__all__ = [
    # Logging
    "log",
    "log_success",
    "log_warning",
    "log_error",
    "log_info",
    "log_processing",
    "log_model_start",
    "log_model_complete",
    "log_model_error",
    "log_file_complete",
    # Timing
    "measure_time",
    "save_timing_results",
    "print_timing_summary",
    # File utils
    "save_html",
    "save_markdown",
]