"""File I/O utilities for saving and loading documents."""

from pathlib import Path
from .html_utils import normalize_html_content


def save_html(html, pdf_path, output_dir):
    """
    Save HTML content to file with proper normalization.

    Args:
        html: HTML content to save
        pdf_path: Original PDF path (for naming)
        output_dir: Directory to save the HTML file
    """
    output_path = output_dir / pdf_path.with_suffix(".html").name
    html = normalize_html_content(html)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def save_markdown(markdown, pdf_path, output_dir):
    """
    Save Markdown content to file.

    Args:
        markdown: Markdown content to save
        pdf_path: Original PDF path (for naming)
        output_dir: Directory to save the Markdown file
    """
    output_path = output_dir / pdf_path.with_suffix(".md").name
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)