"""Jina rerank model provider."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseRerankModel
from models.factory import register_rerank_provider

logger = logging.getLogger(__name__)


@register_rerank_provider("jina")
class JinaRerankModel(BaseRerankModel):
    """Jina AI rerank model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "jina-reranker-v2-base-multilingual",
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        import requests

        url = "https://api.jina.ai/v1/rerank"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        texts = [doc.get("content", "") for doc in documents]
        data = {
            "model": self._model,
            "query": query,
            "documents": texts,
            "top_n": min(top_k, len(documents)),
        }

        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()

        reranked = []
        for item in result.get("results", []):
            idx = item["index"]
            doc = documents[idx].copy()
            doc["rerank_score"] = item["relevance_score"]
            reranked.append(doc)

        return reranked[:top_k]
