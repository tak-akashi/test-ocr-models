"""Qwen Vision-Language Model - Layout Analysis Mode."""

import io
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
from src.utils.file_utils import save_markdown
from .common import download_models, process_single_page_qwen, get_models_cache


# Default prompt for document processing with layout analysis
DEFAULT_PROMPT = """
これは PDF ドキュメントのページです。構造を維持しながら、すべてのテキストコンテンツを抽出してください。
テーブル、列、見出し、および構造化されたコンテンツに特に注意を払ってください。

テーブルの場合：
1. マークダウンテーブル形式を使用してテーブル構造を維持
2. すべての列ヘッダーと行ラベルを保持
3. 数値データが正確にキャプチャされていることを確認

マルチカラムレイアウトの場合：
1. 左から右へ列を処理
2. 異なる列のコンテンツを明確に区別

チャートやグラフの場合：
1. チャートのタイプを説明
2. 可視の軸ラベル、凡例、データポイントを抽出
3. タイトルやキャプションを抽出

イラストの場合：
1. イラストのタイトルを抽出
2. イラストの内容を説明

段落の区切りと書式を維持してください。
すべての見出し、フッター、ページ番号、脚注を維持してください。

出力は必ずマークダウン形式で行って下さい。
"""


def process_document(file_path, output_dir=None, save=False, prompt=None):
    """
    Process PDF or image file using optimized Qwen2.5-VL with layout analysis.

    Args:
        file_path: Path to PDF or image file
        output_dir: Output directory for results
        save: Whether to save the output to file
        prompt: Custom prompt for processing

    Returns:
        str: Processed content in Markdown format
    """
    file_path = Path(file_path)

    # Use default prompt if not provided
    if prompt is None:
        prompt = DEFAULT_PROMPT

    # Get models cache
    _models_cache = get_models_cache()

    # Download models if not cached
    if 'qwen25vl' not in _models_cache:
        print("Qwen2.5VLモデルがダウンロードされていません。ダウンロードを開始します...")
        download_models()
        _models_cache = get_models_cache()

    model_info = _models_cache['qwen25vl']

    # Check if input is image or PDF
    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}:
        # Process as single image
        image = Image.open(file_path)
        page_output = process_single_page_qwen(model_info, image, 0, 1, prompt)
        response_content = page_output
    else:
        # Process as PDF
        doc = fitz.open(file_path)
        total_pages = len(doc)

        # Process each page
        page_outputs = []

        for page_num in range(total_pages):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Process page
            page_output = process_single_page_qwen(model_info, image, page_num, total_pages, prompt)
            page_outputs.append(page_output)

        # Combine results
        response_content = "\n\n---\n\n".join(page_outputs)
        doc.close()

    if save and output_dir is not None:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(response_content, file_path, output_path)

    return response_content
