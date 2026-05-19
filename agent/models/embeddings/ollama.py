"""Ollama embedding model provider for local models."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider

logger = logging.getLogger(__name__)


@register_embedding_provider("ollama")
class OllamaEmbeddingModel(BaseEmbeddingModel):
    """Ollama embedding model wrapper for local models."""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        **kwargs: Any,
    ):
        self._model = model
        self._base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from ollama import Client
                self._client = Client(host=self._base_url)
            except ImportError:
                raise ImportError("ollama package required: pip install ollama")
        return self._client

    @property
    def dimension(self) -> int:
        # Common Ollama embedding models
        dims = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
        }
        return dims.get(self._model, 768)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        results = []
        for text in texts:
            response = client.embeddings(model=self._model, prompt=text)
            results.append(response["embedding"])
        return results

    def embed_query(self, text: str) -> list[float]:
        client = self._get_client()
        response = client.embeddings(model=self._model, prompt=text)
        return response["embedding"]
