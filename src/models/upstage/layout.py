"""Upstage Document Parse API wrapper."""

import requests
from pathlib import Path

from src.config import get_settings
from src.utils.file_utils import save_html, save_markdown


def process_document(
    file_path: Path,
    output_dir: Path = Path("../output/upstage"),
    model: str | None = None,
    save: bool = True
):
    """
    Process PDF or image file using Upstage Document Parse API.

    Args:
        file_path: Path to PDF or image file (supports JPG, JPEG, PNG, BMP, TIFF, HEIC)
        output_dir: Output directory for results
        model: Model to use (default: from config)
        save: Whether to save the output to file

    Returns:
        dict: Processed content with "html" and "markdown" keys
    """
    settings = get_settings()
    url = settings.upstage.endpoint
    api_key = settings.upstage.api_key
    model = model or settings.upstage.layout_model
    headers = {"Authorization": f"Bearer {api_key}"}

    with open(file_path, "rb") as f:
        files = {"document": f}
        data = {"ocr": "auto", "model": model}
        response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code} - {response.text}")

    response_data = response.json()
    content = response_data["content"]
    html_content = content["html"]
    markdown_content = content.get("markdown", "")

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_html(html_content, file_path, output_path)
        save_markdown(markdown_content, file_path, output_path)

    return {"html": html_content, "markdown": markdown_content}