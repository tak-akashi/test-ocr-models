"""Centralized configuration management using pydantic-settings."""

import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UpstageConfig(BaseModel):
    """Upstage Document Parse API configuration."""

    api_key: Optional[str] = Field(default=None, description="Upstage API key")
    endpoint: str = Field(
        default="https://api.upstage.ai/v1/document-digitization",
        description="Upstage API endpoint",
    )
    layout_model: str = Field(
        default="document-parse-nightly",
        description="Model for layout analysis",
    )
    ocr_model: str = Field(
        default="ocr-nightly",
        description="Model for OCR-only mode",
    )


class AzureConfig(BaseModel):
    """Azure Document Intelligence configuration."""

    endpoint: Optional[str] = Field(default=None, description="Azure endpoint URL")
    api_key: Optional[str] = Field(default=None, description="Azure API key")
    layout_model: str = Field(
        default="prebuilt-layout",
        description="Model for layout analysis",
    )
    ocr_model: str = Field(
        default="prebuilt-read",
        description="Model for OCR-only mode",
    )


class GeminiConfig(BaseModel):
    """Google Gemini API configuration."""

    api_key: Optional[str] = Field(default=None, description="Gemini API key")
    model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model name",
    )
    dpi: int = Field(
        default=200,
        ge=72,
        le=600,
        description="DPI for PDF to image conversion",
    )


class ClaudeConfig(BaseModel):
    """Anthropic Claude API configuration."""

    api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Claude model name",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=200000,
        description="Maximum tokens for response",
    )
    dpi: int = Field(
        default=200,
        ge=72,
        le=600,
        description="DPI for PDF to image conversion",
    )


class QwenConfig(BaseModel):
    """Qwen Vision-Language Model configuration."""

    model: str = Field(
        default="Qwen/Qwen2.5-VL-7B-Instruct",
        description="Qwen model name (HuggingFace path)",
    )
    max_new_tokens: int = Field(
        default=2048,
        ge=1,
        le=8192,
        description="Maximum new tokens to generate",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    do_sample: bool = Field(
        default=False,
        description="Whether to use sampling",
    )


class YomitokuConfig(BaseModel):
    """YOMITOKU OCR configuration."""

    visualize: bool = Field(
        default=True,
        description="Whether to generate visualization images",
    )


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.

    Usage:
        from src.config import get_settings

        settings = get_settings()
        api_key = settings.upstage.api_key
        model = settings.gemini.model
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    upstage: UpstageConfig = Field(default_factory=UpstageConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    gemini: GeminiConfig = Field(default_factory=GeminiConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    qwen: QwenConfig = Field(default_factory=QwenConfig)
    yomitoku: YomitokuConfig = Field(default_factory=YomitokuConfig)

    def __init__(self, **kwargs):
        """Initialize settings with backwards-compatible env var mapping."""
        # Map legacy/flat environment variables to nested structure
        env_mapping = {
            # Upstage
            "UPSTAGE_API_KEY": ("upstage", "api_key"),
            "UPSTAGE_ENDPOINT": ("upstage", "endpoint"),
            "UPSTAGE_LAYOUT_MODEL": ("upstage", "layout_model"),
            "UPSTAGE_OCR_MODEL": ("upstage", "ocr_model"),
            # Azure
            "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT": ("azure", "endpoint"),
            "AZURE_DOCUMENT_INTELLIGENCE_API_KEY": ("azure", "api_key"),
            "AZURE_LAYOUT_MODEL": ("azure", "layout_model"),
            "AZURE_OCR_MODEL": ("azure", "ocr_model"),
            # Gemini
            "GEMINI_API_KEY": ("gemini", "api_key"),
            "GEMINI_MODEL": ("gemini", "model"),
            "GEMINI_DPI": ("gemini", "dpi"),
            # Claude
            "ANTHROPIC_API_KEY": ("claude", "api_key"),
            "CLAUDE_MODEL": ("claude", "model"),
            "CLAUDE_MAX_TOKENS": ("claude", "max_tokens"),
            "CLAUDE_DPI": ("claude", "dpi"),
            # Qwen
            "QWEN_MODEL": ("qwen", "model"),
            "QWEN_MAX_NEW_TOKENS": ("qwen", "max_new_tokens"),
            "QWEN_TEMPERATURE": ("qwen", "temperature"),
            "QWEN_DO_SAMPLE": ("qwen", "do_sample"),
            # Yomitoku
            "YOMITOKU_VISUALIZE": ("yomitoku", "visualize"),
        }

        # Build nested structure from flat env vars
        for env_var, (model, field) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if model not in kwargs:
                    kwargs[model] = {}
                if isinstance(kwargs.get(model), dict):
                    kwargs[model][field] = value

        super().__init__(**kwargs)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).

    Returns:
        Settings: Application settings loaded from environment.

    Example:
        settings = get_settings()
        print(settings.upstage.api_key)
    """
    return Settings()


def clear_settings_cache() -> None:
    """
    Clear the settings cache. Useful for testing.

    Example:
        clear_settings_cache()
        settings = get_settings()  # Reloads from environment
    """
    get_settings.cache_clear()
