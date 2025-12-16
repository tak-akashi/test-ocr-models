"""Upstage Document OCR API wrapper (OCR-only mode)."""

import json
import os
import requests
from pathlib import Path


def process_document(
    file_path: Path,
    output_dir: Path = Path("../output/upstage-ocr"),
    model: str = "ocr-nightly",
    save: bool = True
):
    """
    Process PDF or image file using Upstage OCR API (OCR-only mode).

    This mode focuses on pure OCR text extraction without layout analysis.
    Uses model="ocr" which returns plain text directly.

    Args:
        file_path: Path to PDF or image file (supports JPG, JPEG, PNG, BMP, TIFF, HEIC)
        output_dir: Output directory for results
        model: Model to use (default: ocr)
        save: Whether to save the output to file

    Returns:
        dict: OCR result containing text and page information
    """
    url = "https://api.upstage.ai/v1/document-digitization"
    api_key = os.getenv("UPSTAGE_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {"ocr": "force", "model": model}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    result = response.json()
    # OCR model returns: text, pages, confidence, etc. (no content.html/markdown)
    text = result.get("text", "")

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)

        # Save as plain text
        text_file = output_path / f"{file_path.stem}.txt"
        text_file.write_text(text, encoding="utf-8")

        # Save full JSON response for detailed analysis
        json_file = output_path / f"{file_path.stem}.json"
        json_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    return result
