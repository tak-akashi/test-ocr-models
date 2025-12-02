#!/usr/bin/env python3
"""
Post-processing script for yomitoku-ocr results.
Compares yomitoku-ocr output with ground truth dataset and generates evaluation reports.
"""

import argparse
import csv
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import Levenshtein


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    - Unicode normalization (NFKC)
    - Whitespace normalization
    - Remove leading/trailing whitespace
    """
    if not text:
        return ""

    # Unicode normalization (NFKC: compatibility decomposition followed by canonical composition)
    normalized = unicodedata.normalize("NFKC", text)

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    return normalized.strip()


def extract_and_sort_text(words: list[dict[str, Any]], min_score: float = 0.0) -> tuple[str, dict]:
    """
    Extract text from yomitoku-ocr word objects and sort by reading order.

    Args:
        words: List of word objects from yomitoku-ocr JSON
        min_score: Minimum confidence score threshold (0.0 - 1.0)

    Returns:
        Tuple of (concatenated_text, metadata)
    """
    if not words:
        return "", {"word_count": 0, "avg_det_score": 0.0, "avg_rec_score": 0.0}

    # Filter by confidence score
    filtered_words = [
        w for w in words
        if w.get("det_score", 0) >= min_score and w.get("rec_score", 0) >= min_score
    ]

    if not filtered_words:
        return "", {"word_count": 0, "avg_det_score": 0.0, "avg_rec_score": 0.0}

    # Separate by direction
    horizontal_words = []
    vertical_words = []

    for word in filtered_words:
        direction = word.get("direction", "horizontal")
        points = word.get("points", [])

        if not points or len(points) < 4:
            continue

        # Calculate bounding box center for sorting
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)
        top_y = min(ys)
        left_x = min(xs)

        word_with_coords = {
            "word": word,
            "center_x": center_x,
            "center_y": center_y,
            "top_y": top_y,
            "left_x": left_x,
        }

        if direction == "vertical":
            vertical_words.append(word_with_coords)
        else:
            horizontal_words.append(word_with_coords)

    # Sort horizontal text: top to bottom, left to right
    horizontal_words.sort(key=lambda w: (w["top_y"], w["left_x"]))

    # Sort vertical text: right to left, top to bottom
    # Note: For Japanese vertical text, reading order is typically right-to-left columns
    vertical_words.sort(key=lambda w: (-w["center_x"], w["top_y"]))

    # Combine: typically vertical text first (if present), then horizontal
    # But this depends on document layout - adjust if needed
    sorted_words = vertical_words + horizontal_words

    # Extract text content
    text_parts = [w["word"].get("content", "") for w in sorted_words]
    concatenated_text = "".join(text_parts)

    # Calculate metadata
    det_scores = [w.get("det_score", 0) for w in filtered_words]
    rec_scores = [w.get("rec_score", 0) for w in filtered_words]

    metadata = {
        "word_count": len(filtered_words),
        "avg_det_score": sum(det_scores) / len(det_scores) if det_scores else 0.0,
        "avg_rec_score": sum(rec_scores) / len(rec_scores) if rec_scores else 0.0,
        "min_det_score": min(det_scores) if det_scores else 0.0,
        "min_rec_score": min(rec_scores) if rec_scores else 0.0,
        "max_det_score": max(det_scores) if det_scores else 0.0,
        "max_rec_score": max(rec_scores) if rec_scores else 0.0,
        "horizontal_count": len(horizontal_words),
        "vertical_count": len(vertical_words),
    }

    return concatenated_text, metadata


def calculate_metrics(predicted: str, ground_truth: str) -> dict[str, Any]:
    """
    Calculate evaluation metrics.

    Args:
        predicted: Predicted text
        ground_truth: Ground truth text

    Returns:
        Dictionary of metrics
    """
    # Normalize both texts
    pred_norm = normalize_text(predicted)
    gt_norm = normalize_text(ground_truth)

    # Exact match
    exact_match = pred_norm == gt_norm

    # Levenshtein distance
    edit_distance = Levenshtein.distance(pred_norm, gt_norm)

    # Character Error Rate (CER)
    # CER = (substitutions + deletions + insertions) / total characters in reference
    cer = edit_distance / len(gt_norm) if len(gt_norm) > 0 else 0.0

    return {
        "exact_match": exact_match,
        "edit_distance": edit_distance,
        "cer": cer,
        "predicted_length": len(pred_norm),
        "ground_truth_length": len(gt_norm),
    }


def load_ground_truth(gt_path: Path) -> dict[str, str]:
    """
    Load ground truth dataset.

    Args:
        gt_path: Path to gt_dataset.json

    Returns:
        Dictionary mapping filename to ground truth text
    """
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    # Create lookup dictionary: filename -> ground truth
    gt_lookup = {}
    for entry in gt_data:
        path = entry.get("path", "")
        gt_text = entry.get("gt", "")

        # Extract filename from path (e.g., "cropped_images/batch_0_sample_0.png" -> "batch_0_sample_0")
        filename = Path(path).stem
        gt_lookup[filename] = gt_text

    return gt_lookup


def process_yomitoku_outputs(
    yomitoku_dir: Path,
    gt_lookup: dict[str, str],
    min_score: float = 0.0
) -> list[dict[str, Any]]:
    """
    Process all yomitoku-ocr output files.

    Args:
        yomitoku_dir: Directory containing yomitoku-ocr JSON outputs
        gt_lookup: Ground truth lookup dictionary
        min_score: Minimum confidence score threshold

    Returns:
        List of result dictionaries
    """
    results = []

    # Find all JSON files (pattern: *_0.json)
    json_files = sorted(yomitoku_dir.rglob("*_0.json"))

    for json_file in json_files:
        # Extract base filename (remove _0.json suffix)
        base_filename = json_file.stem.rsplit("_", 1)[0]  # "batch_0_sample_0_0" -> "batch_0_sample_0"

        # Load yomitoku output
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                yomitoku_data = json.load(f)
        except Exception as e:
            print(f"Error loading {json_file}: {e}", file=sys.stderr)
            continue

        # Extract and sort text
        words = yomitoku_data.get("words", [])
        predicted_text, ocr_metadata = extract_and_sort_text(words, min_score)

        # Get ground truth
        ground_truth = gt_lookup.get(base_filename, "")

        if not ground_truth:
            print(f"Warning: No ground truth found for {base_filename}", file=sys.stderr)
            continue

        # Calculate metrics
        metrics = calculate_metrics(predicted_text, ground_truth)

        # Combine results
        result = {
            "filename": base_filename,
            "json_file": str(json_file.relative_to(yomitoku_dir)),
            "predicted": predicted_text,
            "ground_truth": ground_truth,
            **metrics,
            **ocr_metadata,
        }

        results.append(result)

    return results


def generate_summary_statistics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Generate summary statistics from results.

    Args:
        results: List of result dictionaries

    Returns:
        Summary statistics dictionary
    """
    if not results:
        return {}

    total_samples = len(results)
    exact_matches = sum(1 for r in results if r["exact_match"])

    cers = [r["cer"] for r in results]
    edit_distances = [r["edit_distance"] for r in results]

    det_scores = [r["avg_det_score"] for r in results if r["avg_det_score"] > 0]
    rec_scores = [r["avg_rec_score"] for r in results if r["avg_rec_score"] > 0]

    summary = {
        "total_samples": total_samples,
        "exact_matches": exact_matches,
        "accuracy": exact_matches / total_samples if total_samples > 0 else 0.0,
        "avg_cer": sum(cers) / len(cers) if cers else 0.0,
        "avg_edit_distance": sum(edit_distances) / len(edit_distances) if edit_distances else 0.0,
        "avg_det_score": sum(det_scores) / len(det_scores) if det_scores else 0.0,
        "avg_rec_score": sum(rec_scores) / len(rec_scores) if rec_scores else 0.0,
    }

    return summary


def save_json_output(results: list[dict[str, Any]], output_path: Path):
    """Save detailed results as JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved JSON output to: {output_path}")


def save_csv_output(results: list[dict[str, Any]], output_path: Path):
    """Save results as CSV."""
    if not results:
        return

    fieldnames = [
        "filename",
        "exact_match",
        "edit_distance",
        "cer",
        "predicted",
        "ground_truth",
        "word_count",
        "avg_det_score",
        "avg_rec_score",
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved CSV output to: {output_path}")


def save_html_output(results: list[dict[str, Any]], summary: dict[str, Any], output_path: Path):
    """Save results as HTML visualization."""
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YOMITOKU-OCR Evaluation Results</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat {{
            text-align: center;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .comparison {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .comparison.match {{
            border-left: 5px solid #27ae60;
        }}
        .comparison.mismatch {{
            border-left: 5px solid #e74c3c;
        }}
        .filename {{
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .text-comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 15px;
        }}
        .text-box {{
            padding: 15px;
            border-radius: 4px;
            background-color: #f8f9fa;
        }}
        .text-box h3 {{
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 14px;
            color: #666;
        }}
        .text-content {{
            font-family: 'Noto Sans JP', sans-serif;
            line-height: 1.6;
            word-break: break-all;
        }}
        .metrics {{
            margin-top: 15px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 4px;
            font-size: 13px;
        }}
        .metrics span {{
            margin-right: 15px;
        }}
        .match-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .match-badge.yes {{
            background-color: #d4edda;
            color: #155724;
        }}
        .match-badge.no {{
            background-color: #f8d7da;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <h1>YOMITOKU-OCR Evaluation Results</h1>

    <div class="summary">
        <h2>Summary Statistics</h2>
        <div class="summary-grid">
            <div class="stat">
                <div class="stat-label">Total Samples</div>
                <div class="stat-value">{summary.get('total_samples', 0)}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Exact Matches</div>
                <div class="stat-value">{summary.get('exact_matches', 0)}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Accuracy</div>
                <div class="stat-value">{summary.get('accuracy', 0) * 100:.1f}%</div>
            </div>
            <div class="stat">
                <div class="stat-label">Avg CER</div>
                <div class="stat-value">{summary.get('avg_cer', 0) * 100:.1f}%</div>
            </div>
            <div class="stat">
                <div class="stat-label">Avg Det Score</div>
                <div class="stat-value">{summary.get('avg_det_score', 0):.3f}</div>
            </div>
            <div class="stat">
                <div class="stat-label">Avg Rec Score</div>
                <div class="stat-value">{summary.get('avg_rec_score', 0):.3f}</div>
            </div>
        </div>
    </div>

    <h2>Detailed Comparisons</h2>
"""

    for result in results:
        match_class = "match" if result["exact_match"] else "mismatch"
        match_badge_class = "yes" if result["exact_match"] else "no"
        match_text = "✓ Match" if result["exact_match"] else "✗ Mismatch"

        html_content += f"""
    <div class="comparison {match_class}">
        <div class="filename">
            {result['filename']}
            <span class="match-badge {match_badge_class}">{match_text}</span>
        </div>

        <div class="text-comparison">
            <div class="text-box">
                <h3>Ground Truth</h3>
                <div class="text-content">{result['ground_truth']}</div>
            </div>
            <div class="text-box">
                <h3>Predicted</h3>
                <div class="text-content">{result['predicted'] or '<em>(empty)</em>'}</div>
            </div>
        </div>

        <div class="metrics">
            <span><strong>CER:</strong> {result['cer'] * 100:.1f}%</span>
            <span><strong>Edit Distance:</strong> {result['edit_distance']}</span>
            <span><strong>Words:</strong> {result['word_count']}</span>
            <span><strong>Det Score:</strong> {result['avg_det_score']:.3f}</span>
            <span><strong>Rec Score:</strong> {result['avg_rec_score']:.3f}</span>
        </div>
    </div>
"""

    html_content += """
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Saved HTML output to: {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Post-process yomitoku-ocr results and compare with ground truth"
    )
    parser.add_argument(
        "yomitoku_dir",
        type=Path,
        help="Path to yomitoku-ocr output directory (e.g., output/20250125-1430/yomitoku-ocr/)"
    )
    parser.add_argument(
        "--gt-dataset",
        type=Path,
        default=Path("datasets/html_visualization_datatang/gt_dataset.json"),
        help="Path to ground truth dataset JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for results (default: same as yomitoku_dir with _evaluation suffix)"
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0.0,
        help="Minimum confidence score threshold (0.0-1.0, default: 0.0)"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.yomitoku_dir.exists():
        print(f"Error: yomitoku-ocr directory not found: {args.yomitoku_dir}", file=sys.stderr)
        sys.exit(1)

    if not args.gt_dataset.exists():
        print(f"Error: Ground truth dataset not found: {args.gt_dataset}", file=sys.stderr)
        sys.exit(1)

    # Set output directory
    if args.output_dir is None:
        args.output_dir = args.yomitoku_dir.parent / f"{args.yomitoku_dir.name}_evaluation"

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("YOMITOKU-OCR Post-Processing")
    print("=" * 80)
    print(f"Input directory: {args.yomitoku_dir}")
    print(f"Ground truth: {args.gt_dataset}")
    print(f"Output directory: {args.output_dir}")
    print(f"Min confidence score: {args.min_score}")
    print()

    # Load ground truth
    print("Loading ground truth dataset...")
    gt_lookup = load_ground_truth(args.gt_dataset)
    print(f"Loaded {len(gt_lookup)} ground truth entries")
    print()

    # Process yomitoku outputs
    print("Processing yomitoku-ocr outputs...")
    results = process_yomitoku_outputs(args.yomitoku_dir, gt_lookup, args.min_score)
    print(f"Processed {len(results)} samples")
    print()

    if not results:
        print("No results to process. Exiting.")
        sys.exit(0)

    # Generate summary
    summary = generate_summary_statistics(results)

    # Print summary to console
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    print(f"Total Samples:      {summary['total_samples']}")
    print(f"Exact Matches:      {summary['exact_matches']}")
    print(f"Accuracy:           {summary['accuracy'] * 100:.2f}%")
    print(f"Avg CER:            {summary['avg_cer'] * 100:.2f}%")
    print(f"Avg Edit Distance:  {summary['avg_edit_distance']:.2f}")
    print(f"Avg Det Score:      {summary['avg_det_score']:.4f}")
    print(f"Avg Rec Score:      {summary['avg_rec_score']:.4f}")
    print("=" * 80)
    print()

    # Save outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # JSON output
    json_path = args.output_dir / f"results_{timestamp}.json"
    save_json_output(results, json_path)

    # CSV output
    csv_path = args.output_dir / f"results_{timestamp}.csv"
    save_csv_output(results, csv_path)

    # HTML output
    html_path = args.output_dir / f"results_{timestamp}.html"
    save_html_output(results, summary, html_path)

    # Summary JSON
    summary_path = args.output_dir / f"summary_{timestamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Saved summary to: {summary_path}")

    print()
    print("Post-processing complete!")


if __name__ == "__main__":
    main()
