"""Test that all model modules can be imported correctly after refactoring."""

import pytest


class TestModelImports:
    """Test that process_document_layout and process_document_ocr functions can be imported from all model modules."""

    def test_import_upstage_functions(self):
        """Test importing process_document_layout and process_document_ocr from upstage module."""
        from src.models.upstage import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_azure_functions(self):
        """Test importing process_document_layout and process_document_ocr from azure module."""
        from src.models.azure import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_yomitoku_functions(self):
        """Test importing process_document_layout and process_document_ocr from yomitoku module."""
        from src.models.yomitoku import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_gemini_functions(self):
        """Test importing process_document_layout and process_document_ocr from gemini module."""
        from src.models.gemini import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_claude_functions(self):
        """Test importing process_document_layout and process_document_ocr from claude module."""
        from src.models.claude import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_qwen_functions(self):
        """Test importing process_document_layout and process_document_ocr from qwen module."""
        from src.models.qwen import process_document_layout, process_document_ocr
        assert callable(process_document_layout), "process_document_layout should be callable"
        assert callable(process_document_ocr), "process_document_ocr should be callable"

    def test_import_qwen_utilities(self):
        """Test importing Qwen-specific utility functions."""
        from src.models.qwen import initialize_models, optimize_for_speed, clear_model_cache, get_model_info
        assert callable(initialize_models), "initialize_models should be callable"
        assert callable(optimize_for_speed), "optimize_for_speed should be callable"
        assert callable(clear_model_cache), "clear_model_cache should be callable"
        assert callable(get_model_info), "get_model_info should be callable"


class TestRunnerImports:
    """Test that runner scripts import correctly."""

    def test_run_models_imports(self):
        """Test that run_models can be imported."""
        from src import run_models

        # Verify the module exists and has the main function
        assert hasattr(run_models, 'run_selected_models_timed_with_datetime'), \
            "Should have run_selected_models_timed_with_datetime function"
        assert hasattr(run_models, 'main'), "Should have main function"


class TestAllModelsConsistency:
    """Test that all models have consistent interface."""

    def test_all_models_have_layout_and_ocr_functions(self):
        """Verify all model modules export process_document_layout and process_document_ocr functions."""
        models = ['upstage', 'azure', 'yomitoku', 'gemini', 'claude', 'qwen']

        for model_name in models:
            module = __import__(f'src.models.{model_name}', fromlist=['process_document_layout', 'process_document_ocr'])

            assert hasattr(module, 'process_document_layout'), \
                f"{model_name} module should have process_document_layout function"
            assert callable(getattr(module, 'process_document_layout')), \
                f"{model_name}.process_document_layout should be callable"

            assert hasattr(module, 'process_document_ocr'), \
                f"{model_name} module should have process_document_ocr function"
            assert callable(getattr(module, 'process_document_ocr')), \
                f"{model_name}.process_document_ocr should be callable"
