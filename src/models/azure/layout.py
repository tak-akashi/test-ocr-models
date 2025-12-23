"""Azure Document Intelligence wrapper."""

from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentContentFormat
from azure.core.credentials import AzureKeyCredential

from src.config import get_settings
from src.utils.file_utils import save_markdown


def get_azure_client():
    """Get Azure Document Intelligence client."""
    settings = get_settings()
    return DocumentIntelligenceClient(
        endpoint=settings.azure.endpoint,
        credential=AzureKeyCredential(settings.azure.api_key)
    )


def process_document(file_path, output_dir=Path("../output/azure"), save=True):
    """
    Process PDF or image file using Azure Document Intelligence.

    Args:
        file_path: Path to PDF or image file (supports JPEG, PNG, BMP, TIFF, HEIF)
        output_dir: Output directory for results
        save: Whether to save the output to file

    Returns:
        str: Processed content in Markdown format
    """
    settings = get_settings()
    file_path = Path(file_path)
    client = get_azure_client()

    with open(file_path, "rb") as file:
        poller = client.begin_analyze_document(
            model_id=settings.azure.layout_model,
            body=file,
            output_content_format=DocumentContentFormat.MARKDOWN
        )

    result: AnalyzeResult = poller.result()

    if save:
        output_path = output_dir / file_path.parent.name
        output_path.mkdir(parents=True, exist_ok=True)
        save_markdown(result.content, file_path, output_path)

    return result.content