"""Test that all model modules can be imported correctly after refactoring."""

import pytest


class TestModelImports:
    """Test that process_document functions can be imported from all model modules."""

    def test_import_upstage_process_document(self):
        """Test importing process_document from upstage module."""
        from src.models.upstage import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_azure_process_document(self):
        """Test importing process_document from azure_di module."""
        from src.models.azure_di import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_yomitoku_process_document(self):
        """Test importing process_document from yomitoku module."""
        from src.models.yomitoku import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_gemini_process_document(self):
        """Test importing process_document from gemini module."""
        from src.models.gemini import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_claude_process_document(self):
        """Test importing process_document from claude module."""
        from src.models.claude import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_qwen_process_document(self):
        """Test importing process_document from qwen module."""
        from src.models.qwen import process_document
        assert callable(process_document), "process_document should be callable"

    def test_import_qwen_process_document_qwen3(self):
        """Test importing process_document_qwen3 from qwen module."""
        from src.models.qwen import process_document_qwen3
        assert callable(process_document_qwen3), "process_document_qwen3 should be callable"


class TestRunnerImports:
    """Test that runner scripts import with correct aliases."""

    def test_run_models_imports_all_models(self):
        """Test that run_models imports all 6 models with aliases (including Qwen)."""
        from src import run_models

        # All 6 models should be imported
        assert hasattr(run_models, 'process_upstage'), "Should have process_upstage alias"
        assert hasattr(run_models, 'process_azure'), "Should have process_azure alias"
        assert hasattr(run_models, 'process_yomitoku'), "Should have process_yomitoku alias"
        assert hasattr(run_models, 'process_gemini'), "Should have process_gemini alias"
        assert hasattr(run_models, 'process_claude'), "Should have process_claude alias"
        assert hasattr(run_models, 'process_qwen'), "Should have process_qwen alias"

    def test_run_models_qwen_special_functions(self):
        """Test that run_models imports Qwen special functions."""
        from src import run_models

        # Qwen-specific functions should be available
        assert hasattr(run_models, 'initialize_models'), "Should have initialize_models"
        assert hasattr(run_models, 'optimize_for_speed'), "Should have optimize_for_speed"


class TestAllModelsConsistency:
    """Test that all models have consistent interface."""

    def test_all_models_have_process_document(self):
        """Verify all model modules export process_document function."""
        models = ['upstage', 'azure_di', 'yomitoku', 'gemini', 'claude', 'qwen']

        for model_name in models:
            module = __import__(f'src.models.{model_name}', fromlist=['process_document'])
            assert hasattr(module, 'process_document'), \
                f"{model_name} module should have process_document function"
            assert callable(getattr(module, 'process_document')), \
                f"{model_name}.process_document should be callable"
