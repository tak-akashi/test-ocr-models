#!/usr/bin/env python3
"""
Extract text from azure, upstage, yomitoku model outputs.
Generates both per-model and combined comparison outputs.

処理概要:
=========
OCRモデル出力ディレクトリから各モデルの結果ファイルを読み込み、
テキストを抽出してCSV/JSON形式で保存するスクリプト。

対応モデルと入力形式:
- Azure: Markdown (.md) ファイル → プレーンテキストとして抽出
- Upstage: HTML (.html) ファイル → BeautifulSoupでタグを除去してテキスト抽出
- YOMITOKU: JSON (.json) ファイル → paragraphs/wordsから読み取り順でテキスト抽出

出力ファイル:
- 各モデル別: azure_texts.csv/json, upstage_texts.csv/json, yomitoku_texts.csv/json
- 統合比較用: combined_texts.csv/json (全モデルの結果を横並びで比較)

使用例:
    uv run python -m src.utils.aggregate_ocr_texts output/20251202-0942
    uv run python -m src.utils.aggregate_ocr_texts output/20251202-0942 --output-dir results/
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def extract_text_from_markdown(md_content: str) -> str:
    """
    Extract text from Markdown content.

    Args:
        md_content: Markdown content string

    Returns:
        Extracted text with normalized whitespace
    """
    if not md_content or not md_content.strip():
        return ""

    # Markdown is already plain text, just normalize whitespace
    text = " ".join(md_content.split())
    return text.strip()


def extract_text_from_html(html_content: str) -> str:
    """
    Extract text from HTML content using BeautifulSoup.

    Args:
        html_content: HTML content string

    Returns:
        Extracted text with normalized whitespace
    """
    if not html_content or not html_content.strip():
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text
    text = soup.get_text()

    # Normalize whitespace
    text = " ".join(text.split())
    return text.strip()


def extract_text_from_yomitoku_words(words: list[dict[str, Any]]) -> str:
    """
    Extract text from yomitoku JSON word objects, sorted by reading order.

    Args:
        words: List of word objects from yomitoku JSON

    Returns:
        Concatenated text in reading order
    """
    if not words:
        return ""

    # Separate by direction
    horizontal_words = []
    vertical_words = []

    for word in words:
        direction = word.get("direction", "horizontal")
        points = word.get("points", [])

        if not points or len(points) < 4:
            continue

        # Calculate bounding box coordinates for sorting
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        center_x = sum(xs) / len(xs)
        top_y = min(ys)
        left_x = min(xs)

        word_with_coords = {
            "word": word,
            "center_x": center_x,
            "top_y": top_y,
            "left_x": left_x,
        }

        if direction == "vertical":
            vertical_words.append(word_with_coords)
        else:
            horizontal_words.append(word_with_coords)

    # Sort horizontal text: top to bottom, left to right
    horizontal_words.sort(key=lambda w: (w["top_y"], w["left_x"]))

    # Sort vertical text: right to left, top to bottom (Japanese reading order)
    vertical_words.sort(key=lambda w: (-w["center_x"], w["top_y"]))

    # Combine: vertical text first (if present), then horizontal
    sorted_words = vertical_words + horizontal_words

    # Extract text content
    text_parts = [w["word"].get("content", "") for w in sorted_words]
    text = "".join(text_parts)
    # Normalize whitespace (same as Azure/Upstage)
    return " ".join(text.split())


def extract_text_from_yomitoku_paragraphs(paragraphs: list[dict[str, Any]]) -> str:
    """
    Extract text from yomitoku JSON paragraph objects, sorted by order.

    Args:
        paragraphs: List of paragraph objects from yomitoku JSON

    Returns:
        Concatenated text in paragraph order
    """
    if not paragraphs:
        return ""

    # Sort by order field
    sorted_paragraphs = sorted(paragraphs, key=lambda p: p.get("order", 0))

    # Extract contents from each paragraph
    text_parts = [p.get("contents", "") for p in sorted_paragraphs]
    text = "".join(text_parts)
    # Normalize whitespace (same as Azure/Upstage)
    return " ".join(text.split())


def extract_text_from_yomitoku_json(
    data: dict[str, Any],
    source: str = "paragraphs",
) -> str:
    """
    Extract text from yomitoku JSON data.

    Args:
        data: Full yomitoku JSON data
        source: Source to extract from ("paragraphs" or "words")
                Defaults to "paragraphs". Falls back to "words" if paragraphs is empty.

    Returns:
        Extracted text
    """
    if source == "paragraphs":
        paragraphs = data.get("paragraphs", [])
        if paragraphs:
            return extract_text_from_yomitoku_paragraphs(paragraphs)
        # Fallback to words if paragraphs is empty
        words = data.get("words", [])
        return extract_text_from_yomitoku_words(words)
    else:
        words = data.get("words", [])
        return extract_text_from_yomitoku_words(words)


def extract_azure_text(file_path: Path) -> str:
    """Extract text from Azure Markdown output file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return extract_text_from_markdown(content)
    except Exception as e:
        print(f"Error reading Azure file {file_path}: {e}", file=sys.stderr)
        return ""


def extract_text_from_upstage_json(data: dict[str, Any]) -> str:
    """
    Extract text from Upstage JSON output.

    Args:
        data: Upstage JSON data

    Returns:
        Extracted text
    """
    # Try pages[].text first (OCR mode format)
    pages = data.get("pages", [])
    if pages:
        text_parts = [page.get("text", "") for page in pages]
        text = " ".join(text_parts)
        return " ".join(text.split()).strip()

    # Fallback to text field
    text = data.get("text", "")
    return " ".join(text.split()).strip()


def extract_upstage_text(file_path: Path) -> str:
    """Extract text from Upstage output file (HTML or JSON)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Determine format by extension
        if file_path.suffix.lower() == ".json":
            data = json.load(open(file_path, "r", encoding="utf-8"))
            return extract_text_from_upstage_json(data)
        elif file_path.suffix.lower() == ".html":
            return extract_text_from_html(content)
        elif file_path.suffix.lower() == ".txt":
            # Plain text file
            return " ".join(content.split()).strip()
        else:
            # Try HTML parsing as fallback
            return extract_text_from_html(content)
    except Exception as e:
        print(f"Error reading Upstage file {file_path}: {e}", file=sys.stderr)
        return ""


def extract_yomitoku_text(file_path: Path, source: str = "paragraphs") -> str:
    """Extract text from YOMITOKU JSON output file.

    Args:
        file_path: Path to YOMITOKU JSON file
        source: Source to extract from ("paragraphs" or "words")

    Returns:
        Extracted text
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return extract_text_from_yomitoku_json(data, source=source)
    except Exception as e:
        print(f"Error reading YOMITOKU file {file_path}: {e}", file=sys.stderr)
        return ""


def process_azure_outputs(azure_dir: Path) -> dict[str, str]:
    """
    Process all Azure output files.

    Returns:
        Dictionary mapping base filename to extracted text
    """
    results = {}
    md_files = sorted(azure_dir.rglob("*.md"))

    for md_file in md_files:
        base_filename = md_file.stem
        text = extract_azure_text(md_file)
        results[base_filename] = text

    return results


def process_upstage_outputs(upstage_dir: Path) -> dict[str, str]:
    """
    Process all Upstage output files.

    Supports both HTML (layout mode) and JSON (OCR mode) formats.

    Returns:
        Dictionary mapping base filename to extracted text
    """
    results = {}

    # Try HTML files first (layout mode)
    html_files = sorted(upstage_dir.rglob("*.html"))
    for html_file in html_files:
        base_filename = html_file.stem
        if base_filename.endswith("_0"):
            base_filename = base_filename[:-2]

        text = extract_upstage_text(html_file)
        results[base_filename] = text

    # Try JSON files (OCR mode) - only if no HTML found for this file
    json_files = sorted(upstage_dir.rglob("*.json"))
    for json_file in json_files:
        base_filename = json_file.stem
        if base_filename.endswith("_0"):
            base_filename = base_filename[:-2]

        # Skip if already processed via HTML
        if base_filename in results:
            continue

        text = extract_upstage_text(json_file)
        results[base_filename] = text

    return results


def process_yomitoku_outputs(
    yomitoku_dir: Path,
    source: str = "paragraphs",
) -> dict[str, str]:
    """
    Process all YOMITOKU output files.

    Args:
        yomitoku_dir: Directory containing YOMITOKU output files
        source: Source to extract from ("paragraphs" or "words")

    Returns:
        Dictionary mapping base filename to extracted text
    """
    results = {}
    json_files = sorted(yomitoku_dir.rglob("*_0.json"))

    for json_file in json_files:
        # Remove _0 suffix (e.g., "ja_pii_handwriting_0001_0" -> "ja_pii_handwriting_0001")
        base_filename = json_file.stem
        if base_filename.endswith("_0"):
            base_filename = base_filename[:-2]

        text = extract_yomitoku_text(json_file, source=source)
        results[base_filename] = text

    return results


def save_model_csv(results: dict[str, str], output_path: Path):
    """Save model results as CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "text"])
        for filename, text in sorted(results.items()):
            writer.writerow([filename, text])
    print(f"Saved: {output_path}")


def save_model_json(results: dict[str, str], output_path: Path):
    """Save model results as JSON."""
    output_data = [
        {"filename": filename, "text": text}
        for filename, text in sorted(results.items())
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {output_path}")


def save_combined_csv(
    azure_results: dict[str, str],
    upstage_results: dict[str, str],
    yomitoku_results: dict[str, str],
    output_path: Path,
):
    """Save combined results as CSV."""
    # Get all unique filenames
    all_filenames = sorted(
        set(azure_results.keys()) | set(upstage_results.keys()) | set(yomitoku_results.keys())
    )

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "azure", "upstage", "yomitoku"])
        for filename in all_filenames:
            writer.writerow([
                filename,
                azure_results.get(filename, ""),
                upstage_results.get(filename, ""),
                yomitoku_results.get(filename, ""),
            ])
    print(f"Saved: {output_path}")


def save_combined_json(
    azure_results: dict[str, str],
    upstage_results: dict[str, str],
    yomitoku_results: dict[str, str],
    output_path: Path,
):
    """Save combined results as JSON."""
    # Get all unique filenames
    all_filenames = sorted(
        set(azure_results.keys()) | set(upstage_results.keys()) | set(yomitoku_results.keys())
    )

    output_data = []
    for filename in all_filenames:
        output_data.append({
            "filename": filename,
            "azure": azure_results.get(filename, ""),
            "upstage": upstage_results.get(filename, ""),
            "yomitoku": yomitoku_results.get(filename, ""),
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {output_path}")


def find_model_dir(input_dir: Path, model_name: str) -> Path | None:
    """
    Find the model directory, supporting both naming conventions.

    Args:
        input_dir: Root input directory
        model_name: Base model name (e.g., "azure", "upstage", "yomitoku")

    Returns:
        Path to model directory if found, None otherwise
    """
    # Try different naming conventions
    candidates = [
        input_dir / model_name,           # e.g., azure/
        input_dir / f"{model_name}-ocr",  # e.g., azure-ocr/
        input_dir / f"{model_name}_ocr",  # e.g., azure_ocr/
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def detect_datasets(input_dir: Path) -> list[str]:
    """
    Detect dataset subdirectories from model output directories.

    Looks for common subdirectories across azure/, upstage/, yomitoku/ directories.
    Supports both naming conventions (e.g., azure/ and azure-ocr/).

    Args:
        input_dir: Root input directory containing model outputs

    Returns:
        List of dataset names (e.g., ["appen_test_200", "datatang_test_200"])
        Returns empty list if no subdirectories found (flat structure)
    """
    model_names = ["azure", "upstage", "yomitoku"]
    dataset_sets = []

    for model_name in model_names:
        model_dir = find_model_dir(input_dir, model_name)
        if model_dir:
            subdirs = {
                d.name for d in model_dir.iterdir()
                if d.is_dir() and not d.name.startswith(".")
            }
            if subdirs:
                dataset_sets.append(subdirs)

    if not dataset_sets:
        return []

    # Find common datasets across all model directories
    common_datasets = dataset_sets[0]
    for ds in dataset_sets[1:]:
        common_datasets = common_datasets & ds

    return sorted(common_datasets)


def process_dataset(
    input_dir: Path,
    output_dir: Path,
    dataset_name: str | None = None,
):
    """
    Process a single dataset and save outputs.

    Args:
        input_dir: Root input directory
        output_dir: Output directory for this dataset
        dataset_name: Dataset subdirectory name (None for flat structure)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find model directories (supporting both naming conventions)
    azure_base = find_model_dir(input_dir, "azure")
    upstage_base = find_model_dir(input_dir, "upstage")
    yomitoku_base = find_model_dir(input_dir, "yomitoku")

    # Determine final model directories
    if dataset_name:
        azure_dir = azure_base / dataset_name if azure_base else None
        upstage_dir = upstage_base / dataset_name if upstage_base else None
        yomitoku_dir = yomitoku_base / dataset_name if yomitoku_base else None
    else:
        azure_dir = azure_base
        upstage_dir = upstage_base
        yomitoku_dir = yomitoku_base

    # Process each model
    azure_results = {}
    upstage_results = {}
    yomitoku_results = {}

    if azure_dir and azure_dir.exists():
        print(f"  Processing Azure outputs from {azure_dir.name}/...")
        azure_results = process_azure_outputs(azure_dir)
        print(f"    Found {len(azure_results)} files")

        save_model_csv(azure_results, output_dir / "azure_texts.csv")
        save_model_json(azure_results, output_dir / "azure_texts.json")
    else:
        print("  Warning: Azure directory not found")

    if upstage_dir and upstage_dir.exists():
        print(f"  Processing Upstage outputs from {upstage_dir.name}/...")
        upstage_results = process_upstage_outputs(upstage_dir)
        print(f"    Found {len(upstage_results)} files")

        save_model_csv(upstage_results, output_dir / "upstage_texts.csv")
        save_model_json(upstage_results, output_dir / "upstage_texts.json")
    else:
        print("  Warning: Upstage directory not found")

    if yomitoku_dir and yomitoku_dir.exists():
        print(f"  Processing YOMITOKU outputs from {yomitoku_dir.name}/...")
        yomitoku_results = process_yomitoku_outputs(yomitoku_dir)
        print(f"    Found {len(yomitoku_results)} files")

        save_model_csv(yomitoku_results, output_dir / "yomitoku_texts.csv")
        save_model_json(yomitoku_results, output_dir / "yomitoku_texts.json")
    else:
        print("  Warning: YOMITOKU directory not found")

    # Save combined outputs
    print("  Saving combined outputs...")
    save_combined_csv(azure_results, upstage_results, yomitoku_results, output_dir / "combined_texts.csv")
    save_combined_json(azure_results, upstage_results, yomitoku_results, output_dir / "combined_texts.json")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract text from azure, upstage, yomitoku model outputs"
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Path to output directory (e.g., output/20251202-0942)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for extracted texts (default: {input_dir}/_extracted)",
    )

    args = parser.parse_args()

    # Validate input directory
    if not args.input_dir.exists():
        print(f"Error: Input directory not found: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # Set base output directory
    if args.output_dir is None:
        base_output_dir = args.input_dir / "_extracted"
    else:
        base_output_dir = args.output_dir

    print("=" * 60)
    print("Text Extraction")
    print("=" * 60)
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {base_output_dir}")
    print()

    # Detect datasets
    datasets = detect_datasets(args.input_dir)

    if datasets:
        # Process each dataset separately
        print(f"Detected {len(datasets)} dataset(s): {', '.join(datasets)}")
        print()

        for dataset_name in datasets:
            print(f"[Dataset: {dataset_name}]")
            output_dir = base_output_dir / dataset_name
            process_dataset(args.input_dir, output_dir, dataset_name)
            print()
    else:
        # Flat structure - process as before
        print("No dataset subdirectories detected, processing flat structure")
        print()
        process_dataset(args.input_dir, base_output_dir, None)

    print("=" * 60)
    print("Extraction complete!")
    print(f"Output files saved to: {base_output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
