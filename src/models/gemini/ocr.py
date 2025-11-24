"""Gemini 2.5 Flash API wrapper - OCR-only Mode."""

import os
import io
from pathlib import Path
from google import genai
from google.genai import types
from pdf2image import convert_from_path
from src.utils.file_utils import save_markdown


# Simplified OCR-only prompt
DEFAULT_PROMPT = """
これは PDF ドキュメントのページです。すべてのテキストコンテンツを読み順に抽出してください。

ルール：
1. テキストを読み順（上から下、左から右）で抽出
2. 段落区切りを維持
3. 見出しやフッター、ページ番号も含める
4. 表はプレーンテキストとして読み順で抽出（表構造は保持しない）
5. シンプルなマークダウン形式で出力

レイアウト構造や複雑な書式設定は不要です。テキスト内容の正確な抽出に集中してください。
"""


def process_document(file_path, output_dir=Path("../output/gemini-ocr"), save=True, prompt=None):
    """
    Process PDF or image file using Gemini 2.5 Flash with OCR-only mode.

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
