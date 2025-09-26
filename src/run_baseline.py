"""Main script for running baseline document processing tests."""

import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from models.upstage import run_upstage
from models.azure_di import run_azure_di
from models.yomitoku import run_yomitoku
from models.gemini import run_gemini
from models.qwen import (
    run_qwen25vl_optimized,
    run_qwen3vl_optimized,
    initialize_models,
    clear_model_cache,
    optimize_for_speed
)
from utils.timing import measure_time, save_timing_results, print_timing_summary


def run_baseline(file_list):
    """
    Run all baseline models on the given files.

    Args:
        file_list: List of PDF file paths to process
    """
    for file_path in file_list:
        print(f"Processing {file_path}...")

        # Upstage Document Parse
        run_upstage(file_path, output_dir=Path("../output/upstage"), save=True)
        print("Processing Upstage/Document Parse... done")

        # Azure Document Intelligence
        run_azure_di(file_path, output_dir=Path("../output/azure"), save=True)
        print("Processing Azure/Document Intelligence... done")

        # YOMITOKU
        run_yomitoku(file_path, output_dir=Path("../output/yomitoku"), save=True)
        print("Processing YOMITOKU... done")

        # Gemini 2.5 Flash
        run_gemini(file_path, output_dir=Path("../output/gemini"), save=True)
        print("Processing Gemini 2.5 Flash... done")


def run_baseline_timed_with_datetime(file_list, base_output_dir=None):
    """
    Run baseline processing with timing and datetime-based output folders.

    Args:
        file_list: List of PDF file paths to process
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
        "output_base_dir": str(base_output_dir),
        "results": []
    }

    for file_idx, file_path in enumerate(file_list):
        file_path = Path(file_path)
        print(f"Processing {file_path}... ({file_idx + 1}/{len(file_list)})")

        file_result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "models": {}
        }

        # Upstage/Document Parse
        print("  Processing Upstage/Document Parse...")
        try:
            _, exec_time = measure_time(run_upstage, file_path,
                                       output_dir=base_output_dir / "upstage", save=True)
            file_result["models"]["upstage"] = {
                "status": "success",
                "execution_time": exec_time
            }
            print(f"    Upstage completed in {exec_time:.2f} seconds")
        except Exception as e:
            file_result["models"]["upstage"] = {
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
            print(f"    Upstage failed: {e}")

        # Azure Document Intelligence
        print("  Processing Azure/Document Intelligence...")
        try:
            _, exec_time = measure_time(run_azure_di, file_path,
                                       output_dir=base_output_dir / "azure", save=True)
            file_result["models"]["azure"] = {
                "status": "success",
                "execution_time": exec_time
            }
            print(f"    Azure completed in {exec_time:.2f} seconds")
        except Exception as e:
            file_result["models"]["azure"] = {
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
            print(f"    Azure failed: {e}")

        # YOMITOKU
        print("  Processing YOMITOKU...")
        try:
            _, exec_time = measure_time(run_yomitoku, file_path,
                                       output_dir=base_output_dir / "yomitoku", save=True)
            file_result["models"]["yomitoku"] = {
                "status": "success",
                "execution_time": exec_time
            }
            print(f"    YOMITOKU completed in {exec_time:.2f} seconds")
        except Exception as e:
            file_result["models"]["yomitoku"] = {
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
            print(f"    YOMITOKU failed: {e}")

        # Gemini 2.5 Flash
        print("  Processing Gemini 2.5 Flash...")
        try:
            _, exec_time = measure_time(run_gemini, file_path,
                                       output_dir=base_output_dir / "gemini", save=True)
            file_result["models"]["gemini"] = {
                "status": "success",
                "execution_time": exec_time
            }
            print(f"    Gemini completed in {exec_time:.2f} seconds")
        except Exception as e:
            file_result["models"]["gemini"] = {
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
            print(f"    Gemini failed: {e}")

        timing_data["results"].append(file_result)
        print(f"  File {file_idx + 1} completed\n")

    # Save timing results
    save_timing_results(timing_data, str(base_output_dir / "timing_results"))

    # Print summary
    print_timing_summary(timing_data)

    print(f"\n出力フォルダ: {base_output_dir}")
    return timing_data


def run_qwen(file_list):
    """
    Run Qwen models on the given files.

    Args:
        file_list: List of PDF file paths to process
    """
    initialize_models()

    for file_path in file_list:
        file_path = Path(file_path)
        run_qwen25vl_optimized(file_path, output_dir=Path("../output/qwen25vl"), save=True)
        # Note: Qwen3VL is commented out in original code
        # run_qwen3vl_optimized(file_path, output_dir=Path("../output/qwen3vl"), save=True)


def run_qwen_timed_with_datetime(file_list, base_output_dir=None):
    """
    Run Qwen models with timing and datetime-based output folders.

    Args:
        file_list: List of PDF file paths to process
        base_output_dir: Base output directory

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
        "output_base_dir": str(base_output_dir),
        "results": []
    }

    # Initialize models
    print("モデルを初期化中...")
    initialize_models()

    for file_idx, file_path in enumerate(file_list):
        file_path = Path(file_path)
        print(f"Processing {file_path}... ({file_idx + 1}/{len(file_list)})")

        file_result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "models": {}
        }

        # Qwen2.5VL
        print("  Processing Qwen2.5VL...")
        try:
            _, exec_time = measure_time(run_qwen25vl_optimized, file_path,
                                       output_dir=base_output_dir / "qwen25vl", save=True)
            file_result["models"]["qwen25vl"] = {
                "status": "success",
                "execution_time": exec_time
            }
            print(f"    Qwen2.5VL completed in {exec_time:.2f} seconds")
        except Exception as e:
            file_result["models"]["qwen25vl"] = {
                "status": "error",
                "error": str(e),
                "execution_time": 0
            }
            print(f"    Qwen2.5VL failed: {e}")

        timing_data["results"].append(file_result)
        print(f"  File {file_idx + 1} completed\n")

    # Save timing results
    save_timing_results(timing_data, str(base_output_dir / "timing_results"))

    # Print summary
    print_timing_summary(timing_data)

    print(f"\n出力フォルダ: {base_output_dir}")
    return timing_data


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run baseline document processing tests")
    parser.add_argument("input", nargs="+", help="Input PDF file(s) or directory")
    parser.add_argument("--models", nargs="+",
                       choices=["upstage", "azure", "yomitoku", "gemini", "qwen25vl", "all"],
                       default=["all"],
                       help="Models to run (default: all)")
    parser.add_argument("--output-dir", type=str, default="../output",
                       help="Base output directory (default: ../output)")
    parser.add_argument("--timing", action="store_true",
                       help="Enable timing measurement")
    parser.add_argument("--qwen-only", action="store_true",
                       help="Run only Qwen models")
    parser.add_argument("--optimize", action="store_true",
                       help="Apply speed optimizations for Qwen models")

    args = parser.parse_args()

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

    # Apply optimizations if requested
    if args.optimize:
        optimize_for_speed()

    # Run processing
    if args.qwen_only:
        if args.timing:
            run_qwen_timed_with_datetime(pdf_files, args.output_dir)
        else:
            run_qwen(pdf_files)
    else:
        if args.timing:
            run_baseline_timed_with_datetime(pdf_files, args.output_dir)
        else:
            run_baseline(pdf_files)


if __name__ == "__main__":
    main()