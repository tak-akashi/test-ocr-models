"""Main script for PDF preprocessing operations."""

import sys
from pathlib import Path

# Add project root to Python path when running from src directory
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import argparse
from src.preprocess.pdf import (
    extract_pages,
    split_pdf_pages,
    display_pdf_pages,
    pdf_to_images
)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="PDF preprocessing utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract pages command
    extract_parser = subparsers.add_parser("extract", help="Extract specific pages from PDF")
    extract_parser.add_argument("input", type=str, help="Input PDF file")
    extract_parser.add_argument("--pages", nargs="+", type=int, required=True,
                               help="Page numbers to extract (1-based)")
    extract_parser.add_argument("--output-dir", type=str,
                               help="Output directory (default: same as input)")

    # Split pages command
    split_parser = subparsers.add_parser("split", help="Split PDF into individual pages")
    split_parser.add_argument("input", type=str, help="Input PDF file")
    split_parser.add_argument("--output-dir", type=str,
                             help="Output directory (default: {input_name}_split_pages)")

    # Convert to images command
    images_parser = subparsers.add_parser("images", help="Convert PDF pages to images")
    images_parser.add_argument("input", type=str, help="Input PDF file")
    images_parser.add_argument("--output-dir", type=str,
                              help="Output directory (default: {input_name}_images)")
    images_parser.add_argument("--dpi-scale", type=float, default=2.0,
                              help="DPI scale factor (default: 2.0)")

    # Display pages command
    display_parser = subparsers.add_parser("display", help="Display PDF pages")
    display_parser.add_argument("input", type=str, help="Input PDF file")
    display_parser.add_argument("--pages", nargs="+", type=int,
                               help="Page numbers to display (default: all)")
    display_parser.add_argument("--dpi-scale", type=float, default=2.0,
                               help="DPI scale factor (default: 2.0)")

    # Process multiple PDFs command
    batch_parser = subparsers.add_parser("batch", help="Process multiple PDFs")
    batch_parser.add_argument("input_dir", type=str, help="Input directory containing PDFs")
    batch_parser.add_argument("--operation", choices=["extract", "split", "images"],
                             default="split", help="Operation to perform")
    batch_parser.add_argument("--pages", nargs="+", type=int,
                             help="Page numbers for extract operation")
    batch_parser.add_argument("--output-dir", type=str,
                             help="Base output directory")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Execute commands
    if args.command == "extract":
        input_path = Path(args.input)
        output_path = extract_pages(input_path, args.pages, args.output_dir)
        print(f"Extraction complete: {output_path}")

    elif args.command == "split":
        input_path = Path(args.input)
        output_paths = split_pdf_pages(input_path, args.output_dir)
        print(f"Split into {len(output_paths)} files")

    elif args.command == "images":
        input_path = Path(args.input)
        output_paths = pdf_to_images(input_path, args.output_dir, args.dpi_scale)
        print(f"Converted to {len(output_paths)} images")

    elif args.command == "display":
        input_path = Path(args.input)
        display_pdf_pages(input_path, args.pages, dpi_scale=args.dpi_scale)

    elif args.command == "batch":
        input_dir = Path(args.input_dir)
        pdf_files = list(input_dir.glob("**/*.pdf"))
        print(f"Found {len(pdf_files)} PDF files")

        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file}")

            if args.operation == "extract":
                if args.pages is None:
                    print("  Skipping: No pages specified for extraction")
                    continue
                output_dir = Path(args.output_dir) if args.output_dir else None
                extract_pages(pdf_file, args.pages, output_dir)

            elif args.operation == "split":
                output_dir = Path(args.output_dir) / pdf_file.stem if args.output_dir else None
                split_pdf_pages(pdf_file, output_dir)

            elif args.operation == "images":
                output_dir = Path(args.output_dir) / pdf_file.stem if args.output_dir else None
                pdf_to_images(pdf_file, output_dir)

        print("\nBatch processing complete")


if __name__ == "__main__":
    main()