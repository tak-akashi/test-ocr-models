"""YOMITOKU OCR processing wrapper."""

import cv2
import nest_asyncio
from pathlib import Path
from yomitoku import DocumentAnalyzer
from yomitoku.data.functions import load_pdf

# Enable asyncio in Jupyter environments
nest_asyncio.apply()


def run_yomitoku(pdf_path, output_dir=Path("../output/yomitoku"), save=True):
    """
    Process PDF using YOMITOKU OCR.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        save: Whether to save the output to file

    Returns:
        list: List of processing results for each page
    """
    analyzer = DocumentAnalyzer(visualize=True, device="cpu")

    # Load PDF file
    imgs = load_pdf(pdf_path)
    output_results = []

    for i, img in enumerate(imgs):
        results, ocr_vis, layout_vis = analyzer(img)

        if save:
            # Create output directory
            parent_path = output_dir / pdf_path.parent.name
            parent_path.mkdir(parents=True, exist_ok=True)

            # Export HTML results
            output_path = parent_path / (pdf_path.name.split(".")[0] + f"_{i}.html")
            results.to_html(str(output_path), img=img)

            # Save visualization images
            output_ocr_path = parent_path / (pdf_path.name.split(".")[0] + f"_ocr_{i}.jpg")
            cv2.imwrite(str(output_ocr_path), ocr_vis)

            output_layout_path = parent_path / (pdf_path.name.split(".")[0] + f"_layout_{i}.jpg")
            cv2.imwrite(str(output_layout_path), layout_vis)

        output_results.append(results)

    return output_results