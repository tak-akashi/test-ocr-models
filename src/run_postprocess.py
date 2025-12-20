"""Main script for OCR postprocessing and evaluation operations."""

import argparse
import sys
from pathlib import Path

# Add project root to Python path when running from src directory
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="OCR postprocessing and evaluation utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run postprocess upstage output/20250125-1430/upstage-ocr/
  uv run postprocess azure output/20250125-1430/azure-ocr/
  uv run postprocess yomitoku-ocr output/20250125-1430/yomitoku-ocr/
  uv run postprocess yomitoku-layout output/20250125-1430/yomitoku/
  uv run postprocess generic temp/ocr_results.json
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upstage postprocessing
    upstage_parser = subparsers.add_parser(
        "upstage",
        help="Evaluate Upstage OCR results against ground truth"
    )
    upstage_parser.add_argument(
        "input_dir",
        type=str,
        help="Path to upstage-ocr output directory"
    )
    upstage_parser.add_argument(
        "--gt-dataset",
        type=str,
        default="datasets/html_visualization_datatang/gt_dataset.json",
        help="Path to ground truth dataset JSON file"
    )
    upstage_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: input_dir with _evaluation suffix)"
    )

    # Azure postprocessing
    azure_parser = subparsers.add_parser(
        "azure",
        help="Evaluate Azure OCR results against ground truth"
    )
    azure_parser.add_argument(
        "input_dir",
        type=str,
        help="Path to azure-ocr output directory"
    )
    azure_parser.add_argument(
        "--gt-dataset",
        type=str,
        default="datasets/html_visualization_datatang/gt_dataset.json",
        help="Path to ground truth dataset JSON file"
    )
    azure_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: input_dir with _evaluation suffix)"
    )

    # Yomitoku OCR postprocessing
    yomitoku_ocr_parser = subparsers.add_parser(
        "yomitoku-ocr",
        help="Evaluate Yomitoku OCR results against ground truth"
    )
    yomitoku_ocr_parser.add_argument(
        "input_dir",
        type=str,
        help="Path to yomitoku-ocr output directory"
    )
    yomitoku_ocr_parser.add_argument(
        "--gt-dataset",
        type=str,
        default="datasets/html_visualization_datatang/gt_dataset.json",
        help="Path to ground truth dataset JSON file"
    )
    yomitoku_ocr_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: input_dir with _evaluation suffix)"
    )
    yomitoku_ocr_parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum confidence score threshold (0.0-1.0, default: 0.0)"
    )

    # Yomitoku Layout postprocessing
    yomitoku_layout_parser = subparsers.add_parser(
        "yomitoku-layout",
        help="Evaluate Yomitoku Layout results against ground truth"
    )
    yomitoku_layout_parser.add_argument(
        "input_dir",
        type=str,
        help="Path to yomitoku layout output directory"
    )
    yomitoku_layout_parser.add_argument(
        "--gt-dataset",
        type=str,
        default="datasets/html_visualization_datatang/gt_dataset.json",
        help="Path to ground truth dataset JSON file"
    )
    yomitoku_layout_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: input_dir with _evaluation_layout suffix)"
    )

    # Generic OCR postprocessing
    generic_parser = subparsers.add_parser(
        "generic",
        help="Evaluate generic OCR results (JSON format) against ground truth"
    )
    generic_parser.add_argument(
        "ocr_results",
        type=str,
        help="Path to OCR results JSON file"
    )
    generic_parser.add_argument(
        "--gt-dataset",
        type=str,
        default="datasets/html_visualization_appen/gt_dataset.json",
        help="Path to ground truth dataset JSON file"
    )
    generic_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for results (default: same as input with _evaluation suffix)"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Execute commands
    if args.command == "upstage":
        from src.postprocess.upstage import (
            load_ground_truth,
            process_upstage_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
        )
        _run_evaluation(
            args,
            load_ground_truth,
            process_upstage_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
            "UPSTAGE-OCR",
        )

    elif args.command == "azure":
        from src.postprocess.azure import (
            load_ground_truth,
            process_azure_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
        )
        _run_evaluation(
            args,
            load_ground_truth,
            process_azure_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
            "AZURE-OCR",
        )

    elif args.command == "yomitoku-ocr":
        from src.postprocess.yomitoku_ocr import (
            load_ground_truth,
            process_yomitoku_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
        )
        _run_yomitoku_ocr_evaluation(args)

    elif args.command == "yomitoku-layout":
        from src.postprocess.yomitoku_layout import (
            load_ground_truth,
            process_yomitoku_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
        )
        _run_evaluation(
            args,
            load_ground_truth,
            process_yomitoku_outputs,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
            "YOMITOKU-LAYOUT",
            output_suffix="_evaluation_layout",
        )

    elif args.command == "generic":
        from src.postprocess.generic_ocr import (
            load_ground_truth,
            load_ocr_results,
            process_results,
            generate_summary_statistics,
            save_json_output,
            save_csv_output,
            save_html_output,
        )
        _run_generic_evaluation(args)


def _run_evaluation(
    args,
    load_ground_truth,
    process_outputs,
    generate_summary_statistics,
    save_json_output,
    save_csv_output,
    save_html_output,
    model_name: str,
    output_suffix: str = "_evaluation",
):
    """Common evaluation workflow for most models."""
    import json
    from datetime import datetime

    input_dir = Path(args.input_dir)
    gt_path = Path(args.gt_dataset)

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    if not gt_path.exists():
        print(f"Error: Ground truth dataset not found: {gt_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else input_dir.parent / f"{input_dir.name}{output_suffix}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"{model_name} Post-Processing")
    print("=" * 80)
    print(f"Input directory: {input_dir}")
    print(f"Ground truth: {gt_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Load ground truth
    print("Loading ground truth dataset...")
    gt_lookup = load_ground_truth(gt_path)
    print(f"Loaded {len(gt_lookup)} ground truth entries")
    print()

    # Process outputs
    print(f"Processing {model_name.lower()} outputs...")
    results = process_outputs(input_dir, gt_lookup)
    print(f"Processed {len(results)} samples")
    print()

    if not results:
        print("No results to process. Exiting.")
        sys.exit(0)

    # Generate and print summary
    summary = generate_summary_statistics(results)
    _print_summary(summary)

    # Save outputs
    _save_outputs(results, summary, output_dir, save_json_output, save_csv_output, save_html_output)

    print()
    print("Post-processing complete!")


def _run_yomitoku_ocr_evaluation(args):
    """Yomitoku OCR specific evaluation with min_score parameter."""
    import json
    from datetime import datetime
    from src.postprocess.yomitoku_ocr import (
        load_ground_truth,
        process_yomitoku_outputs,
        generate_summary_statistics,
        save_json_output,
        save_csv_output,
        save_html_output,
    )

    input_dir = Path(args.input_dir)
    gt_path = Path(args.gt_dataset)

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    if not gt_path.exists():
        print(f"Error: Ground truth dataset not found: {gt_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else input_dir.parent / f"{input_dir.name}_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("YOMITOKU-OCR Post-Processing")
    print("=" * 80)
    print(f"Input directory: {input_dir}")
    print(f"Ground truth: {gt_path}")
    print(f"Output directory: {output_dir}")
    print(f"Min confidence score: {args.min_score}")
    print()

    # Load ground truth
    print("Loading ground truth dataset...")
    gt_lookup = load_ground_truth(gt_path)
    print(f"Loaded {len(gt_lookup)} ground truth entries")
    print()

    # Process outputs with min_score
    print("Processing yomitoku-ocr outputs...")
    results = process_yomitoku_outputs(input_dir, gt_lookup, args.min_score)
    print(f"Processed {len(results)} samples")
    print()

    if not results:
        print("No results to process. Exiting.")
        sys.exit(0)

    # Generate and print summary
    summary = generate_summary_statistics(results)
    _print_summary(summary)

    # Save outputs
    _save_outputs(results, summary, output_dir, save_json_output, save_csv_output, save_html_output)

    print()
    print("Post-processing complete!")


def _run_generic_evaluation(args):
    """Generic OCR evaluation workflow."""
    import json
    from datetime import datetime
    from src.postprocess.generic_ocr import (
        load_ground_truth,
        load_ocr_results,
        process_results,
        generate_summary_statistics,
        save_json_output,
        save_csv_output,
        save_html_output,
    )

    ocr_results_path = Path(args.ocr_results)
    gt_path = Path(args.gt_dataset)

    if not ocr_results_path.exists():
        print(f"Error: OCR results file not found: {ocr_results_path}", file=sys.stderr)
        sys.exit(1)

    if not gt_path.exists():
        print(f"Error: Ground truth dataset not found: {gt_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else ocr_results_path.parent / f"{ocr_results_path.stem}_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("OCR Post-Processing")
    print("=" * 80)
    print(f"OCR results: {ocr_results_path}")
    print(f"Ground truth: {gt_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Load ground truth
    print("Loading ground truth dataset...")
    gt_lookup = load_ground_truth(gt_path)
    print(f"Loaded {len(gt_lookup)} ground truth entries")
    print()

    # Load OCR results
    print("Loading OCR results...")
    ocr_results = load_ocr_results(ocr_results_path)
    print(f"Loaded {len(ocr_results)} OCR results")
    print()

    # Process results
    print("Processing results...")
    results = process_results(ocr_results, gt_lookup)
    print(f"Processed {len(results)} samples")
    print()

    if not results:
        print("No results to process. Exiting.")
        sys.exit(0)

    # Generate and print summary
    summary = generate_summary_statistics(results)
    _print_summary(summary)

    # Save outputs
    _save_outputs(results, summary, output_dir, save_json_output, save_csv_output, save_html_output)

    print()
    print("Post-processing complete!")


def _print_summary(summary: dict):
    """Print summary statistics to console."""
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"Total Samples:      {summary.get('total_samples', 0)}")
    print(f"Exact Matches:      {summary.get('exact_matches', 0)}")
    print(f"Accuracy:           {summary.get('accuracy', 0) * 100:.2f}%")
    print(f"Avg CER:            {summary.get('avg_cer', 0) * 100:.2f}%")
    print(f"Avg Edit Distance:  {summary.get('avg_edit_distance', 0):.2f}")

    # Model-specific metrics
    if "avg_det_score" in summary:
        print(f"Avg Det Score:      {summary['avg_det_score']:.4f}")
    if "avg_rec_score" in summary:
        print(f"Avg Rec Score:      {summary['avg_rec_score']:.4f}")
    if "avg_paragraph_count" in summary:
        print(f"Avg Paragraphs:     {summary['avg_paragraph_count']:.2f}")
    if "avg_table_count" in summary:
        print(f"Avg Tables:         {summary['avg_table_count']:.2f}")

    print("=" * 80)
    print()


def _save_outputs(results, summary, output_dir, save_json_output, save_csv_output, save_html_output):
    """Save evaluation outputs."""
    import json
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON output
    json_path = output_dir / f"results_{timestamp}.json"
    save_json_output(results, json_path)

    # CSV output
    csv_path = output_dir / f"results_{timestamp}.csv"
    save_csv_output(results, csv_path)

    # HTML output
    html_path = output_dir / f"results_{timestamp}.html"
    save_html_output(results, summary, html_path)

    # Summary JSON
    summary_path = output_dir / f"summary_{timestamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved summary to: {summary_path}")


if __name__ == "__main__":
    main()
