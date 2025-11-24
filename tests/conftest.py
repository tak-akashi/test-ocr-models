"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_pdf_path():
    """Return path to sample PDF file in data folder."""
    pdf_path = Path("data/あいおい生命_masked.pdf")
    if not pdf_path.exists():
        pytest.skip(f"Sample PDF not found: {pdf_path}")
    return pdf_path


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for tests."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_output_"))
    yield temp_dir
    # Cleanup after test
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_pdf_path(tmp_path):
    """Create a mock PDF file path (file doesn't need to exist for basic tests)."""
    return tmp_path / "mock_document.pdf"
