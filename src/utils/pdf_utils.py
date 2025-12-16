"""
PDF utilities.

処理概要:
=========
PDFファイルをOCR処理の前に加工するためのユーティリティ関数群。
ページ抽出、分割、画像変換などの前処理機能を提供。

主な機能:
- extract_pages: 指定ページのみを抽出して新しいPDFを作成
- split_pdf_pages: PDFを1ページずつ個別ファイルに分割
- display_pdf_pages: PDFページをJupyter等で画像として表示
- pdf_to_images: PDFの各ページをPNG画像として保存

使用例:
    from src.utils.pdf_utils import extract_pages, split_pdf_pages, pdf_to_images

    # 特定ページを抽出
    extract_pages("input.pdf", [1, 3, 5], output_dir="output/")

    # 全ページを個別PDFに分割
    split_pdf_pages("input.pdf", output_dir="output/")

    # PDFを画像に変換
    pdf_to_images("input.pdf", output_dir="output/", dpi_scale=2.0)

CLIからの使用:
    uv run preprocess extract input.pdf --pages 1 2 3
    uv run preprocess split input.pdf
    uv run preprocess images input.pdf --dpi-scale 2.0
"""

import fitz  # PyMuPDF
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image
import io


def extract_pages(pdf_path, page_numbers, output_dir=None):
    """
    Extract specific pages from a PDF file.

    Args:
        pdf_path: Path to input PDF file
        page_numbers: List of page numbers to extract (1-based)
        output_dir: Optional output directory for extracted PDF

    Returns:
        Path: Path to extracted PDF file
    """
    pdf_path = Path(pdf_path)
    pdf_document = fitz.open(pdf_path)

    # Get total page count
    total_pages = pdf_document.page_count

    # Convert to 0-based indices and filter valid pages
    valid_pages = [p - 1 for p in page_numbers if 0 < p <= total_pages]
    invalid_pages = [p for p in page_numbers if p <= 0 or p > total_pages]

    # Display warnings for invalid pages
    for page_num in invalid_pages:
        print(f"Warning: Page {page_num} does not exist in the document (total pages: {total_pages})")

    # Get extracted page numbers (1-based)
    extracted_pages = [p + 1 for p in valid_pages]

    # Create output path
    if output_dir is None:
        output_dir = pdf_path.parent

    page_list_str = "-".join(map(str, extracted_pages))
    output_path = Path(output_dir) / f"{pdf_path.stem}_pages_{page_list_str}.pdf"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create new PDF document
    new_doc = fitz.open()

    # Add specified pages to new document
    for page_num in valid_pages:
        new_doc.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)

    # Save extracted PDF
    new_doc.save(output_path)
    new_doc.close()
    pdf_document.close()

    print(f"Pages {extracted_pages} extracted to: {output_path}")
    return output_path


def split_pdf_pages(pdf_path, output_dir=None):
    """
    Split a PDF into individual page files.

    Args:
        pdf_path: Path to input PDF file
        output_dir: Output directory for split pages

    Returns:
        list: List of paths to individual page PDFs
    """
    pdf_path = Path(pdf_path)

    # Create output directory
    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_split_pages"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Open PDF document
    pdf_document = fitz.open(pdf_path)
    output_paths = []

    # Save each page as individual PDF
    for page_num in range(pdf_document.page_count):
        # Create single page document
        single_page_doc = fitz.open()

        # Insert current page
        single_page_doc.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)

        # Create filename
        page_number = page_num + 1  # Convert to 1-based
        single_page_filename = f"page_{page_number:03d}.pdf"
        single_page_path = output_dir / single_page_filename

        # Save single page PDF
        single_page_doc.save(single_page_path)
        single_page_doc.close()

        output_paths.append(single_page_path)
        print(f"Page {page_number} saved to: {single_page_path}")

    pdf_document.close()

    print(f"\n全{len(output_paths)}ページが個別のPDFファイルとして保存されました。")
    print(f"保存先ディレクトリ: {output_dir}")

    return output_paths


def display_pdf_pages(pdf_path, page_numbers=None, figsize=(10, 14), dpi_scale=2):
    """
    Display PDF pages as images.

    Args:
        pdf_path: Path to PDF file
        page_numbers: List of page numbers to display (1-based), None for all
        figsize: Figure size for display
        dpi_scale: Scale factor for image resolution
    """
    pdf_document = fitz.open(pdf_path)

    if page_numbers is None:
        pages_to_display = range(pdf_document.page_count)
    else:
        # Convert to 0-based indices
        pages_to_display = [p - 1 for p in page_numbers if 0 < p <= pdf_document.page_count]

    for page_num in pages_to_display:
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale))
        img_data = pix.pil_tobytes(format="PNG")

        img = Image.open(io.BytesIO(img_data))

        plt.figure(figsize=figsize)
        plt.imshow(img)
        plt.axis('off')
        plt.title(f'Page {page_num + 1}')
        plt.show()

    pdf_document.close()


def pdf_to_images(pdf_path, output_dir=None, dpi_scale=2):
    """
    Convert PDF pages to image files.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for images
        dpi_scale: Scale factor for image resolution

    Returns:
        list: List of paths to saved image files
    """
    pdf_path = Path(pdf_path)

    # Create output directory
    if output_dir is None:
        output_dir = pdf_path.parent / f"{pdf_path.stem}_images"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Open PDF document
    pdf_document = fitz.open(pdf_path)
    output_paths = []

    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi_scale, dpi_scale))
        img_data = pix.pil_tobytes(format="PNG")

        img = Image.open(io.BytesIO(img_data))

        # Save image
        page_number = page_num + 1
        image_path = output_dir / f"page_{page_number:03d}.png"
        img.save(image_path)

        output_paths.append(image_path)
        print(f"Page {page_number} saved as image: {image_path}")

    pdf_document.close()

    return output_paths