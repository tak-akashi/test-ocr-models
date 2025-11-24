"""Qwen Vision-Language Model wrappers."""

import os
import io
import torch
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, AutoModelForImageTextToText
from qwen_vl_utils import process_vision_info
from src.utils.file_utils import save_markdown


# Global model cache
_models_cache = {}


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

イラストの場合：
1. イラストのタイトルを抽出
2. イラストの内容を説明

段落の区切りと書式を維持してください。
すべての見出し、フッター、ページ番号、脚注を維持してください。

出力は必ずマークダウン形式で行って下さい。
"""


def _select_device_and_dtype():
    """Select device and data type for model."""
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        dtype = torch.float16
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        dtype = torch.float16
    else:
        device = torch.device("cpu")
        dtype = torch.float32
    return device, dtype


def download_models():
    """Download and cache Qwen models."""
    print("Qwen2.5VLモデルをダウンロード中...")
    device, dtype = _select_device_and_dtype()

    # Check for accelerate availability
    try:
        import accelerate
        use_device_map = True
        print("accelerateが利用可能です。device_mapを使用します。")
    except ImportError:
        use_device_map = False
        print("accelerateが利用できません。device_mapを使用せずにモデルを読み込みます。")

    # Download Qwen2.5VL model
    try:
        if use_device_map and device.type != "cpu":
            qwen25vl_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2.5-VL-7B-Instruct",
                dtype=dtype,
                device_map="auto"
            )
        else:
            qwen25vl_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                "Qwen/Qwen2.5-VL-7B-Instruct",
                dtype=dtype
            )
            qwen25vl_model = qwen25vl_model.to(device)

        qwen25vl_processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

        _models_cache['qwen25vl'] = {
            'model': qwen25vl_model,
            'processor': qwen25vl_processor,
            'device': device,
            'dtype': dtype
        }
        print("Qwen2.5VLモデルのダウンロード完了")

    except Exception as e:
        print(f"Qwen2.5VLモデルのダウンロードに失敗しました: {e}")
        raise

    print("モデルのダウンロードが完了しました！")


def initialize_models():
    """Initialize models (run once at startup)."""
    print("モデルを初期化中...")
    download_models()
    print("初期化完了！")


def clear_model_cache():
    """Clear model cache to free memory."""
    global _models_cache
    _models_cache.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("モデルキャッシュをクリアしました")


def optimize_for_speed():
    """Apply optimization settings for speed."""
    # PyTorch optimization settings
    torch.backends.cudnn.benchmark = True  # CUDA optimization
    torch.backends.cudnn.deterministic = False  # Speed priority

    # Memory efficiency
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("速度最適化設定を適用しました")


def get_model_info():
    """Get current model cache status."""
    print("=== モデルキャッシュ状態 ===")
    for model_name, info in _models_cache.items():
        print(f"{model_name}: 読み込み済み")
        print(f"  デバイス: {info['device']}")
        print(f"  データ型: {info['dtype']}")
    if not _models_cache:
        print("モデルは読み込まれていません")


def process_single_page_qwen(model_info, image, page_num, total_pages, prompt=DEFAULT_PROMPT):
    """Process a single page using Qwen model."""
    model = model_info['model']
    processor = model_info['processor']
    device = model_info['device']

    # Build messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt + f"\n\n（これはページ {page_num + 1}/{total_pages} です）"}
            ]
        }
    ]

    # Prepare prompt
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)

    # Prepare inputs for batch processing
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}

    # Run inference with optimized parameters
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False,
            temperature=0.1,
            pad_token_id=processor.tokenizer.eos_token_id,
            use_cache=True
        )

    generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)]
    output_text = processor.batch_decode(generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)

    return f"<!-- ページ {page_num + 1} -->\n{output_text[0]}"


def process_document(file_path, output_dir=None, save=False, prompt=None):
    """
    Process PDF or image file using optimized Qwen2.5-VL.

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

    # Download models if not cached
    if 'qwen25vl' not in _models_cache:
        print("Qwen2.5VLモデルがダウンロードされていません。ダウンロードを開始します...")
        download_models()

    model_info = _models_cache['qwen25vl']

    # Check if input is image or PDF
    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}:
        # Process as single image
        image = Image.open(file_path)
        page_output = process_single_page_qwen(model_info, image, 0, 1, prompt)
        response_content = page_output
    else:
        # Process as PDF (existing logic)
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


def process_document_qwen3(pdf_path, output_dir=None, save=False, prompt=None):
    """
    Process PDF using optimized Qwen3-VL.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        save: Whether to save the output to file
        prompt: Custom prompt for processing

    Returns:
        str: Processed content in Markdown format
    """
    # Use default prompt if not provided
    if prompt is None:
        prompt = DEFAULT_PROMPT

    # Download models if not cached
    if 'qwen3vl' not in _models_cache:
        print("Qwen3VLモデルがダウンロードされていません。ダウンロードを開始します...")
        # Note: Qwen3VL download is commented out in original code
        raise NotImplementedError("Qwen3VL model download is not implemented")

    model_info = _models_cache['qwen3vl']

    # Open PDF
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    # Process each page
    page_outputs = []

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        # Process page
        page_output = process_single_page_qwen(model_info, image, page_num, total_pages, prompt)
        page_outputs.append(page_output)

    # Combine results
    response_content = "\n\n---\n\n".join(page_outputs)

    if save and output_dir is not None:
        output_path = output_dir / pdf_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(response_content, pdf_path, output_path)

    doc.close()
    return response_content