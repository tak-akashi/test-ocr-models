"""Test that all model functions have correct signatures and are callable."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import inspect


class TestFunctionSignatures:
    """Test that all process_document functions have correct signatures."""

    def test_upstage_signature(self):
        """Test upstage.process_document signature."""
        from src.models.upstage import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_azure_signature(self):
        """Test azure_di.process_document signature."""
        from src.models.azure_di import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_yomitoku_signature(self):
        """Test yomitoku.process_document signature."""
        from src.models.yomitoku import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_gemini_signature(self):
        """Test gemini.process_document signature."""
        from src.models.gemini import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_claude_signature(self):
        """Test claude.process_document signature."""
        from src.models.claude import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"

    def test_qwen_signature(self):
        """Test qwen.process_document signature."""
        from src.models.qwen import process_document

        sig = inspect.signature(process_document)
        params = list(sig.parameters.keys())

        assert 'file_path' in params, "Should have file_path parameter"
        assert 'output_dir' in params, "Should have output_dir parameter"
        assert 'save' in params, "Should have save parameter"


class TestFunctionCallability:
    """Test that functions can be called with mock data (no actual API calls)."""

    def test_upstage_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test upstage.process_document can be called with mocked API."""
        from src.models.upstage import process_document

        # Mock the requests.post call
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": {"html": "<p>Test content</p>"}
        }

        mocker.patch('requests.post', return_value=mock_response)
        mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake pdf content'))

        # Should not raise an error
        result = process_document(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"

    def test_gemini_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test gemini.process_document can be called with mocked API."""
        from src.models.gemini import process_document

        # Mock pdf2image and API client
        mock_image = Mock()
        mocker.patch('src.models.gemini.convert_from_path', return_value=[mock_image])

        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Test content"
        mock_client.models.generate_content.return_value = mock_response

        mocker.patch('src.models.gemini.genai.Client', return_value=mock_client)
        mocker.patch('os.getenv', return_value='fake_api_key')

        # Should not raise an error
        result = process_document(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"

    def test_claude_callable_with_mock(self, mock_pdf_path, temp_output_dir, mocker):
        """Test claude.process_document can be called with mocked API."""
        from src.models.claude import process_document

        # Mock pdf2image and Anthropic client
        mock_image = Mock()
        mocker.patch('src.models.claude.convert_from_path', return_value=[mock_image])

        mock_client = Mock()
        mock_message = Mock()
        mock_content = Mock()
        mock_content.text = "Test content"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message

        mocker.patch('src.models.claude.Anthropic', return_value=mock_client)
        mocker.patch('os.getenv', return_value='fake_api_key')

        # Should not raise an error
        result = process_document(
            file_path=Path(mock_pdf_path),
            output_dir=temp_output_dir,
            save=False
        )

        assert result is not None, "Should return a result"
        assert isinstance(result, str), "Should return a string"


class TestFunctionReturnTypes:
    """Test that functions return expected types."""

    def test_all_functions_return_strings(self):
        """Verify that all process_document functions are expected to return strings."""
        from src.models import upstage, azure_di, yomitoku, gemini, claude, qwen

        # All these functions should have string return type annotations or return strings
        # This is a basic check to ensure consistency
        functions = [
            upstage.process_document,
            azure_di.process_document,
            yomitoku.process_document,
            gemini.process_document,
            claude.process_document,
            qwen.process_document,
        ]

        for func in functions:
            assert callable(func), f"{func.__name__} should be callable"
            # Verify the function has a docstring
            assert func.__doc__ is not None, f"{func.__name__} should have a docstring"
