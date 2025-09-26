"""Upstage Document Parse API wrapper."""

import os
import requests
from pathlib import Path
from ..utils.file_utils import save_html, save_markdown


def run_upstage(pdf_path, output_dir=Path("../output/upstage"), type="html", save=True):
    """
    Process PDF using Upstage Document Parse API.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        type: Output type ("html" or "markdown")
        save: Whether to save the output to file

    Returns:
        str: Processed content (HTML or Markdown)
    """
    url = "https://api.upstage.ai/v1/document-digitization"
    api_key = os.getenv("UPSTAGE_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(pdf_path, "rb") as f:
        files = {"document": f}
        data = {"ocr": "auto", "model": "document-parse-nightly"}
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
        output_path = output_dir / pdf_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        if type == "html":
            save_html(content, pdf_path, output_path)
        elif type == "markdown":
            save_markdown(content, pdf_path, output_path)

    return content