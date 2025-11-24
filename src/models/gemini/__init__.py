"""Gemini 2.5 Flash API wrapper."""

from .layout import process_document as process_document_layout
from .ocr import process_document as process_document_ocr

__all__ = [
    "process_document_layout",
    "process_document_ocr",
]
