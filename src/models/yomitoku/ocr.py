"""YOMITOKU AI-OCR processing wrapper (OCR-only mode)."""

# Import logging utilities first to suppress third-party logs
import src.utils.logging  # noqa: F401 - imported for side effects

import os
import tempfile
from pathlib import Path

import cv2
import nest_asyncio
from PIL import Image
from yomitoku import OCR  # OCR-only class (not DocumentAnalyzer)
from yomitoku.data.functions import load_pdf

from src.config import get_settings
from src.utils.device import get_device

# Enable asyncio in Jupyter environments
nest_asyncio.apply()


def _convert_tif_to_png(tif_path):
    """
    Convert TIF/TIFF image to PNG format.

    Args:
        tif_path: Path to TIF/TIFF file

    Returns:
        str: Path to temporary PNG file
    """
    with Image.open(tif_path) as img:
        # Convert to RGB if necessary (TIFF can be in various modes)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Create temporary PNG file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(temp_fd)  # Close file descriptor, we'll use the path

        # Save as PNG
        img.save(temp_path, 'PNG')

    return temp_path


def process_document(file_path, output_dir=Path("../output/yomitoku-ocr"), save=True):
    """
    Process PDF or image file using YOMITOKU AI-OCR (OCR-only mode).

    Uses the OCR class which performs text detection and recognition
    without layout analysis. This is simpler and faster than DocumentAnalyzer.

    Args:
        file_path: Path to PDF or image file
        output_dir: Output directory for results
        save: Whether to save the output to file

    Returns:
        list: List of processing results for each page/image
    """
    settings = get_settings()
    device = get_device()
    ocr = OCR(visualize=settings.yomitoku.visualize, device=device)
    file_path = Path(file_path)

    temp_png_path = None

    try:
        # Check if input is image or PDF
        if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp'}:
            # Load image using cv2 directly
            img = cv2.imread(str(file_path))
            if img is None:
                raise ValueError(f"Failed to load image file: {file_path}")
            imgs = [img]
        elif file_path.suffix.lower() in {'.tiff', '.tif'}:
            # Convert TIF to PNG first
            print(f"Converting TIF to PNG for yomitoku OCR processing: {file_path.name}")
            temp_png_path = _convert_tif_to_png(str(file_path))
            # Load the converted PNG using cv2 directly
            img = cv2.imread(temp_png_path)
            if img is None:
                raise ValueError(f"Failed to load converted image from TIF file: {file_path}")
            imgs = [img]
        else:
            # Load PDF file
            imgs = load_pdf(str(file_path))

        # Validate that images were loaded
        if not imgs or imgs[0] is None:
            raise ValueError(f"Failed to load images from file: {file_path}")

        output_results = []

        for i, img in enumerate(imgs):
            if img is None:
                print(f"Warning: Skipping null image at index {i} for {file_path.name}")
                continue

            # OCR class returns results and visualization (no layout_vis)
            results, ocr_vis = ocr(img)

            if save:
                # Create output directory
                parent_path = output_dir / file_path.parent.name
                parent_path.mkdir(parents=True, exist_ok=True)

                # Export JSON results (OCR class uses to_json, not to_html)
                output_path = parent_path / (file_path.stem + f"_{i}.json")
                results.to_json(str(output_path))

                # Save OCR visualization image only (no layout visualization in OCR mode)
                output_ocr_path = parent_path / (file_path.stem + f"_ocr_{i}.jpg")
                cv2.imwrite(str(output_ocr_path), ocr_vis)

            output_results.append(results)

        return output_results

    finally:
        # Clean up temporary PNG file if created
        if temp_png_path and os.path.exists(temp_png_path):
            try:
                os.unlink(temp_png_path)
            except Exception as e:
                print(f"Warning: Failed to delete temporary file {temp_png_path}: {e}")
