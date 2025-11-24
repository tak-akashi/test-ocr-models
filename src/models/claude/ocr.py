"""Claude Sonnet 4.5 API wrapper - OCR-only Mode."""

import os
import io
import base64
from pathlib import Path
from anthropic import Anthropic
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


def process_document(file_path, output_dir=Path("../output/claude-ocr"), save=True, prompt=None):
    """
    Process PDF or image file using Claude Sonnet 4.5 with OCR-only mode.

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

    # Get API key and validate
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    client = Anthropic(api_key=api_key)

    # Check if input is image or PDF
    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}:
        # Process as single image
        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        # Determine media type
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        media_type = media_type_map.get(file_path.suffix.lower(), 'image/jpeg')

        # Encode to base64 for Anthropic API
        image_base64 = base64.standard_b64encode(image_bytes).decode('utf-8')

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
                                "media_type": media_type,
                                "data": image_base64,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        output = response.content[0].text
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
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(output, file_path, output_path)

    return output
