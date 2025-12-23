"""Tests for configuration module."""

import os

import pytest

from src.config import (
    Settings,
    UpstageConfig,
    AzureConfig,
    GeminiConfig,
    ClaudeConfig,
    QwenConfig,
    YomitokuConfig,
    get_settings,
    clear_settings_cache,
)


class TestDefaultValues:
    """Test default configuration values."""

    def test_upstage_defaults(self):
        """Test Upstage default values."""
        config = UpstageConfig()
        assert config.api_key is None
        assert config.endpoint == "https://api.upstage.ai/v1/document-digitization"
        assert config.layout_model == "document-parse-nightly"
        assert config.ocr_model == "ocr-nightly"

    def test_azure_defaults(self):
        """Test Azure default values."""
        config = AzureConfig()
        assert config.endpoint is None
        assert config.api_key is None
        assert config.layout_model == "prebuilt-layout"
        assert config.ocr_model == "prebuilt-read"

    def test_gemini_defaults(self):
        """Test Gemini default values."""
        config = GeminiConfig()
        assert config.api_key is None
        assert config.model == "gemini-2.5-flash"
        assert config.dpi == 200

    def test_claude_defaults(self):
        """Test Claude default values."""
        config = ClaudeConfig()
        assert config.api_key is None
        assert config.model == "claude-sonnet-4-5-20250929"
        assert config.max_tokens == 4096
        assert config.dpi == 200

    def test_qwen_defaults(self):
        """Test Qwen default values."""
        config = QwenConfig()
        assert config.model == "Qwen/Qwen2.5-VL-7B-Instruct"
        assert config.max_new_tokens == 2048
        assert config.temperature == 0.1
        assert config.do_sample is False

    def test_yomitoku_defaults(self):
        """Test YOMITOKU default values."""
        config = YomitokuConfig()
        assert config.visualize is True


class TestEnvironmentVariableOverrides:
    """Test environment variable overrides."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear settings cache before and after each test."""
        clear_settings_cache()
        yield
        clear_settings_cache()

    def test_upstage_api_key_override(self, monkeypatch):
        """Test UPSTAGE_API_KEY environment variable."""
        monkeypatch.setenv("UPSTAGE_API_KEY", "test-upstage-key")
        settings = get_settings()
        assert settings.upstage.api_key == "test-upstage-key"

    def test_upstage_layout_model_override(self, monkeypatch):
        """Test UPSTAGE_LAYOUT_MODEL environment variable."""
        monkeypatch.setenv("UPSTAGE_LAYOUT_MODEL", "document-parse-v2")
        settings = get_settings()
        assert settings.upstage.layout_model == "document-parse-v2"

    def test_azure_endpoint_override(self, monkeypatch):
        """Test AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT environment variable."""
        monkeypatch.setenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT", "https://test.azure.com")
        settings = get_settings()
        assert settings.azure.endpoint == "https://test.azure.com"

    def test_gemini_model_override(self, monkeypatch):
        """Test GEMINI_MODEL environment variable."""
        monkeypatch.setenv("GEMINI_MODEL", "gemini-1.5-pro")
        settings = get_settings()
        assert settings.gemini.model == "gemini-1.5-pro"

    def test_claude_max_tokens_override(self, monkeypatch):
        """Test CLAUDE_MAX_TOKENS environment variable."""
        monkeypatch.setenv("CLAUDE_MAX_TOKENS", "8192")
        settings = get_settings()
        assert settings.claude.max_tokens == 8192

    def test_qwen_temperature_override(self, monkeypatch):
        """Test QWEN_TEMPERATURE environment variable."""
        monkeypatch.setenv("QWEN_TEMPERATURE", "0.5")
        settings = get_settings()
        assert settings.qwen.temperature == 0.5

    def test_yomitoku_visualize_override(self, monkeypatch):
        """Test YOMITOKU_VISUALIZE environment variable."""
        monkeypatch.setenv("YOMITOKU_VISUALIZE", "False")
        settings = get_settings()
        assert settings.yomitoku.visualize is False


class TestValidation:
    """Test configuration validation."""

    def test_gemini_dpi_range(self):
        """Test Gemini DPI validation."""
        # Valid DPI
        config = GeminiConfig(dpi=300)
        assert config.dpi == 300

        # Invalid DPI (too low)
        with pytest.raises(ValueError):
            GeminiConfig(dpi=50)

        # Invalid DPI (too high)
        with pytest.raises(ValueError):
            GeminiConfig(dpi=700)

    def test_claude_max_tokens_range(self):
        """Test Claude max_tokens validation."""
        # Valid max_tokens
        config = ClaudeConfig(max_tokens=1000)
        assert config.max_tokens == 1000

        # Invalid max_tokens (too low)
        with pytest.raises(ValueError):
            ClaudeConfig(max_tokens=0)

    def test_qwen_temperature_range(self):
        """Test Qwen temperature validation."""
        # Valid temperature
        config = QwenConfig(temperature=1.0)
        assert config.temperature == 1.0

        # Invalid temperature (too low)
        with pytest.raises(ValueError):
            QwenConfig(temperature=-0.1)

        # Invalid temperature (too high)
        with pytest.raises(ValueError):
            QwenConfig(temperature=2.5)


class TestSettingsSingleton:
    """Test settings singleton behavior."""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear settings cache before and after each test."""
        clear_settings_cache()
        yield
        clear_settings_cache()

    def test_get_settings_returns_same_instance(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_clear_settings_cache_reloads(self, monkeypatch):
        """Test that clearing cache causes reload."""
        # Get initial settings
        settings1 = get_settings()

        # Clear cache and set new environment variable
        clear_settings_cache()
        monkeypatch.setenv("UPSTAGE_API_KEY", "new-key")

        # Get new settings
        settings2 = get_settings()

        # Should be different instance with new value
        assert settings1 is not settings2
        assert settings2.upstage.api_key == "new-key"


class TestSettingsDirectConstruction:
    """Test Settings class direct construction."""

    def test_construct_with_kwargs(self):
        """Test constructing Settings with keyword arguments."""
        settings = Settings(
            upstage={"api_key": "test-key", "layout_model": "custom-model"},
            gemini={"model": "gemini-test", "dpi": 150}
        )
        assert settings.upstage.api_key == "test-key"
        assert settings.upstage.layout_model == "custom-model"
        assert settings.gemini.model == "gemini-test"
        assert settings.gemini.dpi == 150

    def test_nested_config_objects(self):
        """Test that nested configs are proper Pydantic models."""
        settings = Settings()
        assert isinstance(settings.upstage, UpstageConfig)
        assert isinstance(settings.azure, AzureConfig)
        assert isinstance(settings.gemini, GeminiConfig)
        assert isinstance(settings.claude, ClaudeConfig)
        assert isinstance(settings.qwen, QwenConfig)
        assert isinstance(settings.yomitoku, YomitokuConfig)
