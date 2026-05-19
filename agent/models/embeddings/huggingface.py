"""HuggingFace embedding model provider for local models."""
from __future__ import annotations

import logging
from typing import Any, Optional

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider

logger = logging.getLogger(__name__)


@register_embedding_provider("huggingface")
class HuggingFaceEmbeddingModel(BaseEmbeddingModel):
    """HuggingFace embedding model wrapper for sentence-transformers."""

    def __init__(
        self,
        model: str = "sentence-transformers/all-MiniLM-L6-v2",
        **kwargs: Any,
    ):
        self._model_name = model
        self._embeddings = None

    def _get_embeddings(self):
        if self._embeddings is None:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self._embeddings = HuggingFaceEmbeddings(model_name=self._model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers required: pip install sentence-transformers"
                )
        return self._embeddings

    @property
    def dimension(self) -> int:
        dims = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
            "BAAI/bge-large-en": 1024,
            "BAAI/bge-base-en": 768,
            "BAAI/bge-small-en": 384,
        }
        return dims.get(self._model_name, 384)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._get_embeddings()
        return embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        embeddings = self._get_embeddings()
        return embeddings.embed_query(text)
