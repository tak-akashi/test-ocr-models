"""
Postprocessing scripts for OCR evaluation and text aggregation.

Each module compares OCR output with ground truth and generates evaluation reports.

Usage:
    uv run postprocess upstage <output_dir>
    uv run postprocess azure <output_dir>
    uv run postprocess yomitoku-ocr <output_dir>
    uv run postprocess yomitoku-layout <output_dir>
    uv run postprocess generic <ocr_results.json>

    # Text aggregation
    python -m src.postprocess.aggregate <output_dir>
"""

from .aggregate import main as aggregate_main
from .azure import main as azure_main
from .generic_ocr import main as generic_ocr_main
from .upstage import main as upstage_main
from .yomitoku_layout import main as yomitoku_layout_main
from .yomitoku_ocr import main as yomitoku_ocr_main

__all__ = [
    "aggregate_main",
    "upstage_main",
    "azure_main",
    "yomitoku_ocr_main",
    "yomitoku_layout_main",
    "generic_ocr_main",
]
