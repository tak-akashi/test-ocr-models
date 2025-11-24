"""Upstage Document OCR API wrapper (OCR-only mode)."""

import os
import requests
from pathlib import Path
from src.utils.file_utils import save_html, save_markdown


def process_document(
    file_path: Path,
    output_dir: Path = Path("../output/upstage-ocr"),
    model: str = "document-parse-nightly",
    type: str = "html",
    save: bool = True
):
    """
    Process PDF or image file using Upstage OCR API (OCR-only mode).

    This mode focuses on OCR text extraction with minimal layout analysis.
    Uses ocr="force" parameter to ensure OCR is used for text extraction.

    Args:
        file_path: Path to PDF or image file (supports JPG, JPEG, PNG, BMP, TIFF, HEIC)
        output_dir: Output directory for results
        model: Model to use (default: document-parse-nightly)
        type: Output type ("html" or "markdown")
        save: Whether to save the output to file

    Returns:
        str: Processed content (HTML or Markdown)
    """
    url = "https://api.upstage.ai/v1/document-digitization"
    api_key = os.getenv("UPSTAGE_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, "rb") as f:
        files = {"document": f}
        # Use ocr="force" for OCR-only mode instead of "auto"
        data = {"ocr": "force", "model": model}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    if type == "html":
        content = response.json()["content"]["html"]
    elif type == "markdown":
        content = response.json()["content"]["markdown"]
    else:
        raise ValueError(f"Invalid type: {type}. Must be 'html' or 'markdown'")

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        if type == "html":
            save_html(content, file_path, output_path)
        elif type == "markdown":
            save_markdown(content, file_path, output_path)

    return content
