"""Pydantic schemas for model configuration."""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class ModelConfig(BaseModel):
    """Configuration for a single model."""

    model_config = ConfigDict(protected_namespaces=())

    name: str = Field(..., description="Model name/identifier")
    max_tokens: int = Field(default=4096, description="Maximum context tokens")
    model_types: list[str] = Field(default_factory=lambda: ["chat"])
    extra_params: dict[str, Any] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    """Configuration for a model provider."""

    name: str = Field(..., description="Provider display name")
    provider_class: str = Field(..., description="Provider class identifier")
    url: dict[str, str] = Field(default_factory=dict, description="API URLs by region")
    url_suffix: dict[str, str] = Field(default_factory=dict, description="URL suffixes by endpoint type")
    models: list[ModelConfig] = Field(default_factory=list)
    supports: list[str] = Field(
        default_factory=lambda: ["chat"],
        description="Supported model types: chat, embedding, rerank, tts, stt"
    )


class CredentialConfig(BaseModel):
    """Stored credential for a provider."""

    provider: str
    api_key: str
    base_url: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DefaultModelsConfig(BaseModel):
    """Default model selections."""

    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    rerank_model: Optional[str] = None


class ModelTestRequest(BaseModel):
    """Request to test model connectivity."""

    model_config = ConfigDict(protected_namespaces=())

    provider: str
    model: str
    model_type: str = "chat"  # chat, embedding, rerank
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class ModelTestResponse(BaseModel):
    """Response from model connectivity test."""

    model_config = ConfigDict(protected_namespaces=())

    success: bool
    latency_ms: int
    error: Optional[str] = None
    model_info: Optional[dict[str, Any]] = None


class ProviderInfo(BaseModel):
    """Provider information for API response."""

    model_config = ConfigDict(protected_namespaces=())

    name: str
    provider_class: str
    supports: list[str]
    model_count: int
    configured: bool = False


class ModelInfo(BaseModel):
    """Model information for API response."""

    model_config = ConfigDict(protected_namespaces=())

    name: str
    max_tokens: int
    model_types: list[str]
    extra_params: dict[str, Any]
