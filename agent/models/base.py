"""Abstract base classes for model providers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional


class BaseEmbeddingModel(ABC):
    """Abstract base class for embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed a single query."""
        pass

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async embed a list of documents. Default: sync wrapper."""
        return self.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Async embed a single query. Default: sync wrapper."""
        return self.embed_query(text)


class BaseChatModel(ABC):
    """Abstract base class for chat models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass

    @abstractmethod
    def invoke(self, messages: list[dict], **kwargs: Any) -> Any:
        """Invoke the chat model with messages."""
        pass

    @abstractmethod
    def stream(self, messages: list[dict], **kwargs: Any) -> Any:
        """Stream the chat model response."""
        pass

    async def ainvoke(self, messages: list[dict], **kwargs: Any) -> Any:
        """Async invoke. Default: sync wrapper."""
        return self.invoke(messages, **kwargs)

    async def astream(self, messages: list[dict], **kwargs: Any) -> AsyncIterator[Any]:
        """Async stream. Default: sync wrapper."""
        for chunk in self.stream(messages, **kwargs):
            yield chunk


class BaseRerankModel(ABC):
    """Abstract base class for rerank models."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """Rerank documents by relevance to query.

        Args:
            query: The search query
            documents: List of documents with 'content' and 'chunk_id' fields
            top_k: Number of top documents to return

        Returns:
            List of documents with 'rerank_score' field added
        """
        pass
