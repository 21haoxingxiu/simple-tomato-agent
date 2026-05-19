"""Embedding 工厂:
- 支持多模型提供商: OpenAI, ZhipuAI, DashScope, Ollama, Voyage, HuggingFace
- 优先使用 ModelFactory 配置
- 缺 key 时降级 FakeEmbeddings(开发用,保证链路可跑)
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _is_valid_key(key: Optional[str]) -> bool:
    if not key:
        return False
    k = key.strip()
    if k.startswith("sk-placeholder") or k == "sk-your-key-here":
        return False
    return len(k) >= 16


def _detect_provider_from_base_url() -> str:
    """Detect provider from OPENAI_BASE_URL."""
    base_url = os.getenv("OPENAI_BASE_URL", "").lower()
    if "bigmodel.cn" in base_url or "zhipuai" in base_url:
        return "zhipuai"
    if "dashscope" in base_url:
        return "dashscope"
    if "moonshot" in base_url:
        return "moonshot"
    if "mistral" in base_url:
        return "mistral"
    if "deepseek" in base_url:
        return "deepseek"
    return "openai"


@lru_cache(maxsize=1)
def get_embeddings() -> Any:
    """Get embeddings instance using model factory or fallback."""
    provider = os.getenv("EMBEDDING_PROVIDER", "auto").lower()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None

    # Auto-detect provider from base URL
    if provider == "auto":
        provider = _detect_provider_from_base_url()

    # Try to use model factory
    try:
        from models.factory import get_model_factory
        factory = get_model_factory()

        # Set credential if available
        if _is_valid_key(api_key):
            factory.set_credential(provider, api_key)

        logger.info("Using %s embedding model: %s", provider, model)
        return factory.get_embedding_model(provider=provider, model=model)
    except Exception as e:
        logger.warning("Model factory failed, falling back to direct implementation: %s", e)

    # Fallback to direct implementation
    if provider == "zhipuai":
        return _get_zhipuai_embeddings(api_key, model)
    elif provider == "huggingface":
        return _get_huggingface_embeddings(model)
    else:
        return _get_openai_embeddings(api_key, model, base_url)


def _get_openai_embeddings(api_key: str, model: str, base_url: Optional[str]) -> Any:
    """Get OpenAI-compatible embeddings."""
    from langchain_openai import OpenAIEmbeddings

    if not _is_valid_key(api_key):
        logger.warning("OPENAI_API_KEY missing/invalid — using FakeEmbeddings")
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=1536)

    logger.info("Using OpenAIEmbeddings model=%s base_url=%s", model, base_url or "default")
    return OpenAIEmbeddings(model=model, api_key=api_key, base_url=base_url)


def _get_zhipuai_embeddings(api_key: str, model: str) -> Any:
    """Get ZhipuAI embeddings."""
    if not _is_valid_key(api_key):
        logger.warning("ZHIPUAI_API_KEY missing — using FakeEmbeddings")
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=1024)

    # Default to embedding-3 for ZhipuAI
    if model.startswith("text-embedding"):
        model = "embedding-3"
        logger.info("Auto-switched to ZhipuAI embedding model: %s", model)

    try:
        from models.embeddings.zhipuai import ZhipuAIEmbeddingModel
        return ZhipuAIEmbeddingModel(api_key=api_key, model=model)
    except ImportError:
        logger.warning("zhipuai not installed, falling back to OpenAI-compatible")
        return _get_openai_embeddings(api_key, model, "https://open.bigmodel.cn/api/paas/v4/")


def _get_huggingface_embeddings(model: str) -> Any:
    """Get HuggingFace embeddings."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        logger.info("Using HuggingFaceEmbeddings model=%s", model)
        return HuggingFaceEmbeddings(model_name=model)
    except Exception as exc:
        logger.warning("HuggingFace embeddings unavailable: %s — falling back to Fake", exc)
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=384)
