"""Azure Document Intelligence OCR wrapper (OCR-only mode using prebuilt-read model)."""

import os
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentContentFormat
from src.utils.file_utils import save_markdown


def get_azure_client():
    """Get Azure Document Intelligence client."""
    return DocumentIntelligenceClient(
        endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY"))
    )


def process_document(file_path, output_dir=Path("../output/azure-ocr"), save=True):
    """
    Process PDF or image file using Azure Document Intelligence OCR (prebuilt-read model).

    The prebuilt-read model is optimized for text extraction (OCR) and runs at higher
    resolution than Azure Vision Read. It focuses on extracting print and handwritten
    text without complex layout analysis.

    Args:
        file_path: Path to PDF or image file (supports JPEG, PNG, BMP, TIFF, HEIF, PDF)
        output_dir: Output directory for results
        save: Whether to save the output to file

    Returns:
        str: Processed content in Markdown format
    """
    file_path = Path(file_path)
    client = get_azure_client()

    with open(file_path, "rb") as file:
        poller = client.begin_analyze_document(
            model_id="prebuilt-read",  # OCR-only model (not prebuilt-layout)
            body=file,
            output_content_format=DocumentContentFormat.MARKDOWN
        )

    result: AnalyzeResult = poller.result()

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(result.content, file_path, output_path)

    return result.content
