"""DashScope (Alibaba Tongyi) embedding model provider."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider

logger = logging.getLogger(__name__)


@register_embedding_provider("dashscope")
class DashScopeEmbeddingModel(BaseEmbeddingModel):
    """DashScope embedding model wrapper for Alibaba Tongyi."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-v3",
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key

    @property
    def dimension(self) -> int:
        dims = {
            "text-embedding-v1": 1536,
            "text-embedding-v2": 1536,
            "text-embedding-v3": 1024,
        }
        return dims.get(self._model, 1024)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        import dashscope
        from dashscope import TextEmbedding

        dashscope.api_key = self._api_key
        results = []

        for text in texts:
            response = TextEmbedding.call(
                model=self._model,
                input=text,
            )
            if response.status_code == 200:
                results.append(response.output["embeddings"][0]["embedding"])
            else:
                raise RuntimeError(f"DashScope embedding failed: {response.code} - {response.message}")

        return results

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
