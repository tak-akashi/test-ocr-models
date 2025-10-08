"""Claude Sonnet 4.5 API wrapper."""

import os
import io
import base64
from pathlib import Path
from anthropic import Anthropic
from pdf2image import convert_from_path
from src.utils.file_utils import save_markdown


# Default prompt for document processing
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


def run_claude(pdf_path, output_dir=Path("../output/claude"), save=True, prompt=None):
    """
    Process PDF using Claude Sonnet 4.5.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        save: Whether to save the output to file
        prompt: Custom prompt for processing (uses default if None)

    Returns:
        str: Processed content in Markdown format
    """
    # Use default prompt if not provided
    if prompt is None:
        prompt = DEFAULT_PROMPT

    # Convert all pages to images
    images = convert_from_path(pdf_path, dpi=200)

    # Get API key and validate
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    client = Anthropic(api_key=api_key)

    # Process each page
    page_outputs = []

    for i, image in enumerate(images):
        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        image_bytes = img_byte_arr.getvalue()

        # Encode to base64 for Anthropic API
        image_base64 = base64.standard_b64encode(image_bytes).decode('utf-8')

        # Process each page individually
        response = client.messages.create(
            model='claude-sonnet-4-5-20250929',
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt + f"\n\n（これはページ {i+1}/{len(images)} です）"
                        }
                    ]
                }
            ]
        )

        page_outputs.append(f"<!-- ページ {i+1} -->\n{response.content[0].text}")

    # Combine results from all pages
    output = "\n\n---\n\n".join(page_outputs)

    if save:
        output_path = output_dir / pdf_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(output, pdf_path, output_path)

    return output
