"""Voyage AI embedding model provider."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider

logger = logging.getLogger(__name__)


@register_embedding_provider("voyage")
class VoyageEmbeddingModel(BaseEmbeddingModel):
    """Voyage AI embedding model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "voyage-3",
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import voyageai
                self._client = voyageai.Client(api_key=self._api_key)
            except ImportError:
                raise ImportError("voyageai package required: pip install voyageai")
        return self._client

    @property
    def dimension(self) -> int:
        dims = {
            "voyage-3": 1024,
            "voyage-3-large": 1024,
            "voyage-3-lite": 512,
            "voyage-2": 1024,
        }
        return dims.get(self._model, 1024)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        result = client.embed(texts, model=self._model)
        return result.embeddings

    def embed_query(self, text: str) -> list[float]:
        client = self._get_client()
        result = client.embed([text], model=self._model)
        return result.embeddings[0]
