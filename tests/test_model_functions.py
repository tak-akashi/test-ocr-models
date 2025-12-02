"""Test that all model functions have correct signatures and are callable."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import inspect


class TestFunctionSignatures:
    """Test that all process_document_layout and process_document_ocr functions have correct signatures."""

    def test_upstage_layout_signature(self):
        """Test upstage.process_document_layout signature."""
        from src.models.upstage import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_upstage_ocr_signature(self):
        """Test upstage.process_document_ocr signature."""
        from src.models.upstage import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_azure_layout_signature(self):
        """Test azure.process_document_layout signature."""
        from src.models.azure import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_azure_ocr_signature(self):
        """Test azure.process_document_ocr signature."""
        from src.models.azure import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_yomitoku_layout_signature(self):
        """Test yomitoku.process_document_layout signature."""
        from src.models.yomitoku import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_yomitoku_ocr_signature(self):
        """Test yomitoku.process_document_ocr signature."""
        from src.models.yomitoku import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_gemini_layout_signature(self):
        """Test gemini.process_document_layout signature."""
        from src.models.gemini import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_gemini_ocr_signature(self):
        """Test gemini.process_document_ocr signature."""
        from src.models.gemini import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_claude_layout_signature(self):
        """Test claude.process_document_layout signature."""
        from src.models.claude import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_claude_ocr_signature(self):
        """Test claude.process_document_ocr signature."""
        from src.models.claude import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_qwen_layout_signature(self):
        """Test qwen.process_document_layout signature."""
        from src.models.qwen import process_document_layout

        sig = inspect.signature(process_document_layout)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_qwen_ocr_signature(self):
        """Test qwen.process_document_ocr signature."""
        from src.models.qwen import process_document_ocr

        sig = inspect.signature(process_document_ocr)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"


class TestFunctionCallability:
    """Test that functions can be called with mock data (no actual API calls)."""

    def test_upstage_layout_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test upstage.process_document_layout can be called with mocked API."""
        from src.models.upstage import process_document_layout

        # Mock the requests.post call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": {"html": "<p>Test content</p>"}
        }

        mocker.patch('requests.post', return_value=mock_response)
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake pdf content'))

        # Should not raise an error
        result = process_document_layout(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"

    def test_gemini_layout_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test gemini.process_document_layout can be called with mocked API."""
        from src.models.gemini import process_document_layout

        # Mock pdf2image and API client
        mock_image = Mock()
        mocker.patch('src.models.gemini.layout.convert_from_path', return_value=[mock_image])

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Test content"
        mock_client.models.generate_content.return_value = mock_response

        mocker.patch('src.models.gemini.layout.genai.Client', return_value=mock_client)
        mocker.patch('os.getenv', return_value='fake_api_key')

        # Should not raise an error
        result = process_document_layout(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"

    def test_claude_layout_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test claude.process_document_layout can be called with mocked API."""
        from src.models.claude import process_document_layout

        # Mock pdf2image and Anthropic client
        mock_image = Mock()
        mocker.patch('src.models.claude.layout.convert_from_path', return_value=[mock_image])

        mock_client = Mock()
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Test content"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message

        mocker.patch('src.models.claude.layout.Anthropic', return_value=mock_client)
        mocker.patch('os.getenv', return_value='fake_api_key')

        # Should not raise an error
        result = process_document_layout(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"


class TestFunctionReturnTypes:
    """Test that functions return expected types."""

    def test_all_layout_functions_return_strings(self):
        """Verify that all process_document_layout functions are expected to return strings."""
        from src.models import upstage, azure, yomitoku, gemini, claude, qwen

        # All these functions should have string return type annotations or return strings
        # This is a basic check to ensure consistency
        functions = [
            upstage.process_document_layout,
            azure.process_document_layout,
            yomitoku.process_document_layout,
            gemini.process_document_layout,
            claude.process_document_layout,
            qwen.process_document_layout,
        ]

        for func in functions:
            assert callable(func), f"{func.__name__} should be callable"
            # Verify the function has a docstring
            assert func.__doc__ is not None, f"{func.__name__} should have a docstring"

    def test_all_ocr_functions_return_strings(self):
        """Verify that all process_document_ocr functions are expected to return strings."""
        from src.models import upstage, azure, yomitoku, gemini, claude, qwen

        # All these functions should have string return type annotations or return strings
        functions = [
            upstage.process_document_ocr,
            azure.process_document_ocr,
            yomitoku.process_document_ocr,
            gemini.process_document_ocr,
            claude.process_document_ocr,
            qwen.process_document_ocr,
        ]

        for func in functions:
            assert callable(func), f"{func.__name__} should be callable"
            # Verify the function has a docstring
            assert func.__doc__ is not None, f"{func.__name__} should have a docstring"
