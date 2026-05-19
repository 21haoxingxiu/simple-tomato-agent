"""Cohere rerank model provider."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseRerankModel
from models.factory import register_rerank_provider

logger = logging.getLogger(__name__)


@register_rerank_provider("cohere")
class CohereRerankModel(BaseRerankModel):
    """Cohere rerank model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "rerank-multilingual-v3.0",
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(self._api_key)
            except ImportError:
                raise ImportError("cohere package required: pip install cohere")
        return self._client

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        client = self._get_client()
        texts = [doc.get("content", "") for doc in documents]

        response = client.rerank(
            model=self._model,
            query=query,
            documents=texts,
            top_n=min(top_k, len(documents)),
        )

        reranked = []
        for item in response.results:
            idx = item.index
            doc = documents[idx].copy()
            doc["rerank_score"] = item.relevance_score
            reranked.append(doc)

        return reranked[:top_k]
