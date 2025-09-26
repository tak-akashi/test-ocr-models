"""Azure Document Intelligence wrapper."""

import os
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentContentFormat
from ..utils.file_utils import save_markdown


def get_azure_client():
    """Get Azure Document Intelligence client."""
    return DocumentIntelligenceClient(
        endpoint=os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"),
        credential=AzureKeyCredential(os.getenv("AZURE_DOCUMENT_INTELLIGENCE_API_KEY"))
    )


def run_azure_di(pdf_path, output_dir=Path("../output/azure"), save=True):
    """
    Process PDF using Azure Document Intelligence.

    Args:
        pdf_path: Path to PDF file
        output_dir: Output directory for results
        save: Whether to save the output to file

    Returns:
        str: Processed content in Markdown format
    """
    client = get_azure_client()

    with open(pdf_path, "rb") as file:
        poller = client.begin_analyze_document(
            model_id="prebuilt-layout",
            body=file,
            output_content_format=DocumentContentFormat.MARKDOWN
        )

    result: AnalyzeResult = poller.result()

    if save:
        output_path = output_dir / pdf_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(result.content, pdf_path, output_path)

    return result.content