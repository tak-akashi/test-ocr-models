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

# Load environment variables
load_dotenv()

from src.models.upstage import run_upstage
from src.models.azure_di import run_azure_di
from src.models.yomitoku import run_yomitoku
from src.models.gemini import run_gemini
from src.models.claude import run_claude
from src.utils.timing import measure_time, save_timing_results, print_timing_summary


def run_selected_models_timed_with_datetime(file_list, selected_models, base_output_dir=None):
    """
    Run selected models with timing and datetime-based output folders.

    Args:
        file_list: List of PDF file paths to process
        selected_models: List of model names to run
        base_output_dir: Base output directory (defaults to ../output/{timestamp})

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

    # Define model configurations
    model_configs = {
        "upstage": {
            "name": "Upstage/Document Parse",
            "function": run_upstage,
            "output_subdir": "upstage"
        },
        "azure": {
            "name": "Azure/Document Intelligence",
            "function": run_azure_di,
            "output_subdir": "azure"
        },
        "yomitoku": {
            "name": "YOMITOKU",
            "function": run_yomitoku,
            "output_subdir": "yomitoku"
        },
        "gemini": {
            "name": "Gemini 2.5 Flash",
            "function": run_gemini,
            "output_subdir": "gemini"
        },
        "claude": {
            "name": "Claude Sonnet 4.5",
            "function": run_claude,
            "output_subdir": "claude"
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


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run selected document processing models")
    parser.add_argument("input", nargs="*", default=["data"],
                       help="Input PDF file(s) or directory (default: data)")
    parser.add_argument("--models", nargs="+",
                       choices=["upstage", "azure", "yomitoku", "gemini", "claude", "all"],
                       default=["all"],
                       help="Models to run (default: all)")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Base output directory (default: output)")

    args = parser.parse_args()

    # Determine which models to run
    if "all" in args.models:
        selected_models = ["upstage", "azure", "yomitoku", "gemini", "claude"]
    else:
        selected_models = args.models

    print(f"Selected models: {', '.join(selected_models)}\n")

    # Collect PDF files
    pdf_files = []
    for input_path in args.input:
        path = Path(input_path)
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_files.append(path)
        elif path.is_dir():
            pdf_files.extend(path.glob("**/*.pdf"))

    if not pdf_files:
        print("No PDF files found")
        return

    print(f"Found {len(pdf_files)} PDF file(s)")

    # Run selected models with timestamp-based output
    run_selected_models_timed_with_datetime(pdf_files, selected_models, args.output_dir)


if __name__ == "__main__":
    main()
