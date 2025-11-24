"""Qwen Vision-Language Model common utilities."""

import torch
from pathlib import Path
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info


# Global model cache
_models_cache = {}


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


def process_single_page_qwen(model_info, image, page_num, total_pages, prompt):
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


def get_models_cache():
    """Get the global models cache."""
    return _models_cache
