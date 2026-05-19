"""OpenAI embedding model provider."""
from __future__ import annotations

from typing import Any, Optional

from langchain_openai import OpenAIEmbeddings

from models.base import BaseEmbeddingModel
from models.factory import register_embedding_provider


@register_embedding_provider("openai")
class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """OpenAI embedding model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        base_url: Optional[str] = None,
        **kwargs: Any,
    ):
        self._model = model
        self._embeddings = OpenAIEmbeddings(
            model=model,
            api_key=api_key,
            base_url=base_url,
        )

    @property
    def dimension(self) -> int:
        dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dims.get(self._model, 1536)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embeddings.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embeddings.aembed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await self._embeddings.aembed_query(text)
