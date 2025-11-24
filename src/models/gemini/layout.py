"""Gemini 2.5 Flash API wrapper - Layout Analysis Mode."""

import os
import io
from pathlib import Path
from google import genai
from google.genai import types
from pdf2image import convert_from_path
from src.utils.file_utils import save_markdown


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
4. チャートの内容を説明

イラストの場合：
1. イラストのタイトルを抽出
2. イラストの内容を説明

段落の区切りと書式を維持してください。
すべての見出し、フッター、ページ番号、脚注を維持してください。

出力は必ずマークダウン形式で行って下さい。
"""


def process_document(file_path, output_dir=Path("../output/gemini"), save=True, prompt=None):
    """
    Process PDF or image file using Gemini 2.5 Flash with layout analysis.

    Args:
        file_path: Path to PDF or image file
        output_dir: Output directory for results
        save: Whether to save the output to file
        prompt: Custom prompt for processing (uses default if None)

    Returns:
        str: Processed content in Markdown format
    """
    file_path = Path(file_path)

    # Use default prompt if not provided
    if prompt is None:
        prompt = DEFAULT_PROMPT

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Check if input is image or PDF
    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}:
        # Process as single image
        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        # Determine MIME type
        mime_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        mime_type = mime_type_map.get(file_path.suffix.lower(), 'image/jpeg')

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                ),
                prompt
            ]
        )

        output = response.text
    else:
        # Process as PDF (convert all pages to images)
        images = convert_from_path(file_path, dpi=200)

        # Process each page
        page_outputs = []

        for i, image in enumerate(images):
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            image_bytes = img_byte_arr.getvalue()

            # Process each page individually
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg',
                    ),
                    prompt + f"\n\n（これはページ {i+1}/{len(images)} です）"
                ]
            )

            page_outputs.append(f"<!-- ページ {i+1} -->\n{response.text}")

        # Combine results from all pages
        output = "\n\n---\n\n".join(page_outputs)

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(output, file_path, output_path)

    return output
