"""
Preprocessing utilities for PDF and image operations.

Usage:
    # PDF operations (via CLI)
    uv run preprocess extract input.pdf --pages 1 2 3
    uv run preprocess split input.pdf
    uv run preprocess images input.pdf

    # Direct import
    from src.preprocess.pdf import extract_pages, split_pdf_pages, pdf_to_images
    from src.preprocess.deskew import process_image, classify_image
    from src.preprocess.categorize import process_images_by_category
"""

from .pdf import (
    extract_pages,
    split_pdf_pages,
    pdf_to_images,
    display_pdf_pages,
)

__all__ = [
    "extract_pages",
    "split_pdf_pages",
    "pdf_to_images",
    "display_pdf_pages",
]
