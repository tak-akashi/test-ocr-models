"""Script for running selected document processing models."""

import sys
from pathlib import Path

# Add project root to Python path when running from src directory
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import argparse
from datetime import datetime
from dotenv import load_dotenv


from src.models.upstage import (
    process_document_layout as process_upstage_layout,
    process_document_ocr as process_upstage_ocr
)
from src.models.azure import (
    process_document_layout as process_azure_layout,
    process_document_ocr as process_azure_ocr
)
from src.models.yomitoku import (
    process_document_layout as process_yomitoku_layout,
    process_document_ocr as process_yomitoku_ocr
)
from src.models.gemini import (
    process_document_layout as process_gemini_layout,
    process_document_ocr as process_gemini_ocr
)
from src.models.claude import (
    process_document_layout as process_claude_layout,
    process_document_ocr as process_claude_ocr
)
from src.models.qwen import (
    process_document_layout as process_qwen_layout,
    process_document_ocr as process_qwen_ocr,
    initialize_models,
    optimize_for_speed
)
from src.utils.timing import measure_time, save_timing_results, print_timing_summary

# Load environment variables
load_dotenv()

def run_selected_models_timed_with_datetime(file_list, selected_models, base_output_dir=None, optimize=False):
    """
    Run selected models with timing and datetime-based output folders.

    Args:
        file_list: List of document file paths to process (PDFs and images)
        selected_models: List of model names to run
        base_output_dir: Base output directory (defaults to ../output/{timestamp})
        optimize: Apply speed optimizations (for Qwen models)

    Returns:
        dict: Timing data for all processing
    """
    # Create datetime-based output folder
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")

    if base_output_dir is None:
        base_output_dir = Path(f"../output/{timestamp}")
    else:
        base_output_dir = Path(base_output_dir) / timestamp

    base_output_dir.mkdir(parents=True, exist_ok=True)

    timing_data = {
        "timestamp": datetime.now().isoformat(),
        "total_files": len(file_list),
        "selected_models": selected_models,
        "output_base_dir": str(base_output_dir),
        "results": []
    }

    # Initialize Qwen models if selected
    if "qwen" in selected_models or "qwen-ocr" in selected_models:
        print("Qwenモデルを初期化中...")
        initialize_models()

        if optimize:
            print("速度最適化設定を適用中...")
            optimize_for_speed()

    # Define model configurations
    model_configs = {
        "upstage": {
            "name": "Upstage/Document Parse (Layout)",
            "function": process_upstage_layout,
            "output_subdir": "upstage"
        },
        "upstage-ocr": {
            "name": "Upstage/Document OCR",
            "function": process_upstage_ocr,
            "output_subdir": "upstage-ocr"
        },
        "azure": {
            "name": "Azure/Document Intelligence (Layout)",
            "function": process_azure_layout,
            "output_subdir": "azure"
        },
        "azure-ocr": {
            "name": "Azure/Document Intelligence (OCR)",
            "function": process_azure_ocr,
            "output_subdir": "azure-ocr"
        },
        "yomitoku": {
            "name": "YOMITOKU (Layout)",
            "function": process_yomitoku_layout,
            "output_subdir": "yomitoku"
        },
        "yomitoku-ocr": {
            "name": "YOMITOKU (OCR)",
            "function": process_yomitoku_ocr,
            "output_subdir": "yomitoku-ocr"
        },
        "gemini": {
            "name": "Gemini 2.5 Flash (Layout)",
            "function": process_gemini_layout,
            "output_subdir": "gemini"
        },
        "gemini-ocr": {
            "name": "Gemini 2.5 Flash (OCR)",
            "function": process_gemini_ocr,
            "output_subdir": "gemini-ocr"
        },
        "claude": {
            "name": "Claude Sonnet 4.5 (Layout)",
            "function": process_claude_layout,
            "output_subdir": "claude"
        },
        "claude-ocr": {
            "name": "Claude Sonnet 4.5 (OCR)",
            "function": process_claude_ocr,
            "output_subdir": "claude-ocr"
        },
        "qwen": {
            "name": "Qwen2.5VL (Layout)",
            "function": process_qwen_layout,
            "output_subdir": "qwen25vl"
        },
        "qwen-ocr": {
            "name": "Qwen2.5VL (OCR)",
            "function": process_qwen_ocr,
            "output_subdir": "qwen25vl-ocr"
        }
    }

    for file_idx, file_path in enumerate(file_list):
        file_path = Path(file_path)
        print(f"Processing {file_path}... ({file_idx + 1}/{len(file_list)})")

        file_result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "models": {}
        }

        # Process each selected model
        for model_key in selected_models:
            config = model_configs[model_key]
            print(f"  Processing {config['name']}...")

            try:
                _, exec_time = measure_time(
                    config['function'],
                    file_path,
                    output_dir=base_output_dir / config['output_subdir'],
                    save=True
                )
                file_result["models"][model_key] = {
                    "status": "success",
                    "execution_time": exec_time
                }
                print(f"    {config['name']} completed in {exec_time:.2f} seconds")
            except Exception as e:
                file_result["models"][model_key] = {
                    "status": "error",
                    "error": str(e),
                    "execution_time": 0
                }
                print(f"    {config['name']} failed: {e}")

        timing_data["results"].append(file_result)
        print(f"  File {file_idx + 1} completed\n")

    # Always save timing results and print summary
    save_timing_results(timing_data, str(base_output_dir / "timing_results"))
    print_timing_summary(timing_data)

    print(f"\n出力フォルダ: {base_output_dir}")
    return timing_data


def _collect_document_files(input_paths):
    """Collect document files from input paths."""
    SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    document_files = []

    for input_path in input_paths:
        path = Path(input_path)
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            document_files.append(path)
        elif path.is_dir():
            for ext in SUPPORTED_EXTENSIONS:
                document_files.extend(path.glob(f"**/*{ext}"))
                document_files.extend(path.glob(f"**/*{ext.upper()}"))

    return sorted(document_files)


# Model name constants
LAYOUT_MODELS = ["upstage", "azure", "yomitoku", "gemini", "claude", "qwen"]
OCR_MODELS = ["upstage", "azure", "yomitoku", "gemini", "claude", "qwen"]
ALL_MODELS = ["upstage", "upstage-ocr", "azure", "azure-ocr",
              "yomitoku", "yomitoku-ocr", "gemini", "gemini-ocr",
              "claude", "claude-ocr", "qwen", "qwen-ocr"]


def main_layout():
    """Entry point for layout analysis CLI."""
    parser = argparse.ArgumentParser(description="Run layout analysis models")
    parser.add_argument("--input", nargs="*", default=["data"],
                       help="Input PDF/image file(s) or directory (default: data)")
    parser.add_argument("--models", nargs="+",
                       choices=LAYOUT_MODELS + ["all"],
                       default=["upstage"],
                       help="Models to run (default: upstage)")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Base output directory (default: output)")
    parser.add_argument("--optimize", action="store_true",
                       help="Apply speed optimizations (for Qwen models)")
    parser.add_argument("--n-samples", type=int, default=None,
                       help="Process only first N files (default: all)")

    args = parser.parse_args()

    # Determine which models to run
    if "all" in args.models:
        selected_models = LAYOUT_MODELS
    else:
        selected_models = args.models

    print(f"[Layout Analysis] Selected models: {', '.join(selected_models)}\n")

    document_files = _collect_document_files(args.input)
    if args.n_samples is not None:
        document_files = document_files[:args.n_samples]
    if not document_files:
        print("No PDF or image files found")
        return

    pdf_count = sum(1 for f in document_files if f.suffix.lower() == '.pdf')
    image_count = len(document_files) - pdf_count
    print(f"Found {len(document_files)} file(s): {pdf_count} PDF(s), {image_count} image(s)")

    run_selected_models_timed_with_datetime(document_files, selected_models, args.output_dir, args.optimize)


def main_ocr():
    """Entry point for OCR-only CLI."""
    parser = argparse.ArgumentParser(description="Run OCR-only models")
    parser.add_argument("--input", nargs="*", default=["data"],
                       help="Input PDF/image file(s) or directory (default: data)")
    parser.add_argument("--models", nargs="+",
                       choices=OCR_MODELS + ["all"],
                       default=["upstage"],
                       help="Models to run (default: upstage)")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Base output directory (default: output)")
    parser.add_argument("--optimize", action="store_true",
                       help="Apply speed optimizations (for Qwen models)")
    parser.add_argument("--n-samples", type=int, default=None,
                       help="Process only first N files (default: all)")

    args = parser.parse_args()

    # Determine which models to run and add -ocr suffix
    if "all" in args.models:
        selected_models = [f"{m}-ocr" for m in OCR_MODELS]
    else:
        selected_models = [f"{m}-ocr" for m in args.models]

    print(f"[OCR Only] Selected models: {', '.join(selected_models)}\n")

    document_files = _collect_document_files(args.input)
    if args.n_samples is not None:
        document_files = document_files[:args.n_samples]
    if not document_files:
        print("No PDF or image files found")
        return

    pdf_count = sum(1 for f in document_files if f.suffix.lower() == '.pdf')
    image_count = len(document_files) - pdf_count
    print(f"Found {len(document_files)} file(s): {pdf_count} PDF(s), {image_count} image(s)")

    run_selected_models_timed_with_datetime(document_files, selected_models, args.output_dir, args.optimize)


def main():
    """Main entry point for CLI (backward compatible)."""
    parser = argparse.ArgumentParser(description="Run selected document processing models")
    parser.add_argument("--input", nargs="*", default=["data"],
                       help="Input PDF/image file(s) or directory (default: data)")
    parser.add_argument("--models", nargs="+",
                       choices=ALL_MODELS + ["all"],
                       default=["upstage"],
                       help="Models to run (default: upstage)")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Base output directory (default: output)")
    parser.add_argument("--optimize", action="store_true",
                       help="Apply speed optimizations (for Qwen models)")
    parser.add_argument("--n-samples", type=int, default=None,
                       help="Process only first N files (default: all)")

    args = parser.parse_args()

    # Determine which models to run
    if "all" in args.models:
        selected_models = ALL_MODELS
    else:
        selected_models = args.models

    print(f"Selected models: {', '.join(selected_models)}\n")

    document_files = _collect_document_files(args.input)
    if args.n_samples is not None:
        document_files = document_files[:args.n_samples]
    if not document_files:
        print("No PDF or image files found")
        return

    pdf_count = sum(1 for f in document_files if f.suffix.lower() == '.pdf')
    image_count = len(document_files) - pdf_count
    print(f"Found {len(document_files)} file(s): {pdf_count} PDF(s), {image_count} image(s)")

    run_selected_models_timed_with_datetime(document_files, selected_models, args.output_dir, args.optimize)


if __name__ == "__main__":
    main()
