"""ZhipuAI embedding model provider."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider

logger = logging.getLogger(__name__)


@register_embedding_provider("zhipuai")
class ZhipuAIEmbeddingModel(BaseEmbeddingModel):
    """ZhipuAI embedding model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "embedding-3",
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from zhipuai import ZhipuAI
                self._client = ZhipuAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("zhipuai package required: pip install zhipuai")
        return self._client

    @property
    def dimension(self) -> int:
        return 1024  # embedding-3 default

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        results = []
        for text in texts:
            response = client.embeddings.create(
                model=self._model,
                input=text,
            )
            results.append(response.data[0].embedding)
        return results

    def embed_query(self, text: str) -> list[float]:
        client = self._get_client()
        response = client.embeddings.create(
            model=self._model,
            input=text,
        )
        return response.data[0].embedding
