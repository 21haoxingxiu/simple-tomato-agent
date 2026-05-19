"""Model factory for creating provider-specific model instances."""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Type

from models.base import BaseChatModel, BaseEmbeddingModel, BaseRerankModel
from models.schemas import ProviderConfig, ModelConfig

logger = logging.getLogger(__name__)

# Provider class registry
_EMBEDDING_PROVIDERS: dict[str, Type[BaseEmbeddingModel]] = {}
_CHAT_PROVIDERS: dict[str, Type[BaseChatModel]] = {}
_RERANK_PROVIDERS: dict[str, Type[BaseRerankModel]] = {}


def register_embedding_provider(name: str):
    """Decorator to register an embedding provider."""
    def decorator(cls: Type[BaseEmbeddingModel]) -> Type[BaseEmbeddingModel]:
        _EMBEDDING_PROVIDERS[name.lower()] = cls
        return cls
    return decorator


def register_chat_provider(name: str):
    """Decorator to register a chat provider."""
    def decorator(cls: Type[BaseChatModel]) -> Type[BaseChatModel]:
        _CHAT_PROVIDERS[name.lower()] = cls
        return cls
    return decorator


def register_rerank_provider(name: str):
    """Decorator to register a rerank provider."""
    def decorator(cls: Type[BaseRerankModel]) -> Type[BaseRerankModel]:
        _RERANK_PROVIDERS[name.lower()] = cls
        return cls
    return decorator


class ModelFactory:
    """Factory for creating model instances from configuration."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "conf" / "models"
        self._providers: dict[str, ProviderConfig] = {}
        self._credentials: dict[str, str] = {}  # provider -> api_key
        self._defaults: dict[str, str] = {}  # model_type -> model_name
        self._load_configs()

    def _load_configs(self) -> None:
        """Load provider configurations from JSON files."""
        if not self.config_dir.exists():
            logger.warning("Config directory %s does not exist", self.config_dir)
            return

        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                config = ProviderConfig(**data)
                self._providers[config.name.lower()] = config
                logger.debug("Loaded provider config: %s", config.name)
            except Exception as e:
                logger.warning("Failed to load config %s: %s", config_file, e)

        # Load environment variables as fallback
        self._load_env_credentials()

    def _load_env_credentials(self) -> None:
        """Load credentials from environment variables."""
        env_mapping = {
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "zhipuai": "ZHIPUAI_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "dashscope": "DASHSCOPE_API_KEY",
            "voyage": "VOYAGE_API_KEY",
            "jina": "JINA_API_KEY",
            "cohere": "COHERE_API_KEY",
        }
        for provider, env_var in env_mapping.items():
            key = os.getenv(env_var, "").strip()
            if key and len(key) >= 16:
                self._credentials[provider] = key

    def list_providers(self, model_type: Optional[str] = None) -> list[ProviderConfig]:
        """List all available providers, optionally filtered by model type."""
        providers = list(self._providers.values())
        if model_type:
            providers = [p for p in providers if model_type in p.supports]
        return providers

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get a provider configuration by name."""
        return self._providers.get(name.lower())

    def list_models(self, provider: str) -> list[ModelConfig]:
        """List all models for a provider."""
        config = self.get_provider(provider)
        return config.models if config else []

    def get_credential(self, provider: str) -> Optional[str]:
        """Get the API key for a provider."""
        return self._credentials.get(provider.lower())

    def set_credential(self, provider: str, api_key: str) -> None:
        """Set the API key for a provider."""
        self._credentials[provider.lower()] = api_key

    def get_embedding_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseEmbeddingModel:
        """Create an embedding model instance.

        Args:
            provider: Provider name (e.g., 'openai', 'zhipuai')
            model: Model name (e.g., 'text-embedding-3-small')
            api_key: API key override (takes precedence over stored credentials)
            **kwargs: Additional provider-specific arguments

        Returns:
            Embedding model instance
        """
        # Fallback to environment variable
        if not provider:
            provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

        provider = provider.lower()
        cls = _EMBEDDING_PROVIDERS.get(provider)

        if not cls:
            raise ValueError(
                f"Unknown embedding provider: {provider}. "
                f"Available: {list(_EMBEDDING_PROVIDERS.keys())}"
            )

        # Get API key: priority is passed param > stored credential > env var
        if not api_key:
            api_key = self._credentials.get(provider)
        if not api_key:
            # Try common env var fallback
            api_key = os.getenv("OPENAI_API_KEY", "")

        # Get model name
        if not model:
            model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        return cls(api_key=api_key, model=model, **kwargs)

    def get_chat_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """Create a chat model instance.

        Args:
            provider: Provider name (e.g., 'openai', 'deepseek')
            model: Model name (e.g., 'gpt-4o-mini')
            api_key: API key override (takes precedence over stored credentials)
            **kwargs: Additional provider-specific arguments

        Returns:
            Chat model instance
        """
        # Fallback to environment variable
        if not provider:
            provider = os.getenv("LLM_PROVIDER", "openai").lower()

        provider = provider.lower()
        cls = _CHAT_PROVIDERS.get(provider)

        if not cls:
            raise ValueError(
                f"Unknown chat provider: {provider}. "
                f"Available: {list(_CHAT_PROVIDERS.keys())}"
            )

        # Get API key: priority is passed param > stored credential > env var
        if not api_key:
            api_key = self._credentials.get(provider)
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "")

        # Get model name
        if not model:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Get base URL if specified
        base_url = os.getenv("OPENAI_BASE_URL", "") or None

        return cls(api_key=api_key, model=model, base_url=base_url, **kwargs)

    def get_rerank_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseRerankModel:
        """Create a rerank model instance.

        Args:
            provider: Provider name (e.g., 'jina', 'cohere')
            model: Model name
            api_key: API key override (takes precedence over stored credentials)
            **kwargs: Additional provider-specific arguments

        Returns:
            Rerank model instance
        """
        if not provider:
            provider = os.getenv("RERANK_PROVIDER", "jina").lower()

        provider = provider.lower()
        cls = _RERANK_PROVIDERS.get(provider)

        if not cls:
            raise ValueError(
                f"Unknown rerank provider: {provider}. "
                f"Available: {list(_RERANK_PROVIDERS.keys())}"
            )

        # Get API key: priority is passed param > stored credential
        if not api_key:
            api_key = self._credentials.get(provider, "")

        return cls(api_key=api_key, model=model, **kwargs)


# Global factory instance
_factory: Optional[ModelFactory] = None


def get_model_factory() -> ModelFactory:
    """Get the global model factory instance."""
    global _factory
    if _factory is None:
        _factory = ModelFactory()
    return _factory
