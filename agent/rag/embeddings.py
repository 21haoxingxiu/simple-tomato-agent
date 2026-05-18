"""Embedding 工厂:
- 优先 OpenAIEmbeddings(支持智谱 / OneAPI 等 OpenAI 兼容端点,通过 OPENAI_BASE_URL)
- 缺 key 时降级 FakeEmbeddings(开发用,保证链路可跑)
- 未来可扩展 HuggingFaceEmbeddings/BGE
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


def _base_url() -> Optional[str]:
    url = os.getenv("EMBEDDING_BASE_URL", "").strip() or os.getenv(
        "OPENAI_BASE_URL", ""
    ).strip()
    return url or None


@lru_cache(maxsize=1)
def get_embeddings() -> Any:
    provider = os.getenv("EMBEDDING_PROVIDER", "auto").lower()
    api_key = os.getenv("OPENAI_API_KEY", "")

    if provider in ("openai", "auto") and _is_valid_key(api_key):
        from langchain_openai import OpenAIEmbeddings

        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        base = _base_url()
        logger.info("Using OpenAIEmbeddings model=%s base_url=%s", model, base or "default")
        return OpenAIEmbeddings(model=model, api_key=api_key, base_url=base)

    if provider == "huggingface":
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings

            model = os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            logger.info("Using HuggingFaceEmbeddings model=%s", model)
            return HuggingFaceEmbeddings(model_name=model)
        except Exception as exc:
            logger.warning("HuggingFace embeddings unavailable: %s — falling back to Fake", exc)

    from langchain_community.embeddings import FakeEmbeddings

    logger.warning(
        "OPENAI_API_KEY missing/invalid — using FakeEmbeddings(1536) for development only"
    )
    return FakeEmbeddings(size=1536)
