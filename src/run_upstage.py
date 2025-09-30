"""Main script for running baseline document processing tests."""

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
from src.utils.timing import measure_time, save_timing_results, print_timing_summary


MODELS = ["document-parse-nightly", "document-parse-250618"]


def run_comparison(file_list, base_output_dir=None):
    """
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
        for model in MODELS:
            print("  Processing Upstage/Document Parse...")
            try:
                _, exec_time = measure_time(run_upstage, file_path,
                                        output_dir=base_output_dir / "upstage" / model, model=model, save=True)
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


    # Always save timing results and print summary
    save_timing_results(timing_data, str(base_output_dir / "timing_results"))
    print_timing_summary(timing_data)

    print(f"\n出力フォルダ: {base_output_dir}")
    return timing_data



def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run baseline document processing tests")
    parser.add_argument("input", nargs="*", default=["data"],
                       help="Input PDF file(s) or directory (default: data)")
    parser.add_argument("--models", nargs="+",
                       choices=["upstage", "azure", "yomitoku", "gemini", "all"],
                       default=["all"],
                       help="Models to run (default: all)")
    parser.add_argument("--output-dir", type=str, default="output",
                       help="Base output directory (default: output)")

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

    # Run baseline processing with timestamp-based output
    run_comparison(pdf_files, args.output_dir)


if __name__ == "__main__":
    main()