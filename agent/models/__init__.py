"""Model factory and providers for AgentStudio.

Supports multiple LLM, embedding, and rerank providers:
- OpenAI, DeepSeek, ZhipuAI, Moonshot, Mistral, Ollama (LLM)
- OpenAI, ZhipuAI, DashScope, Ollama, Voyage, HuggingFace (Embedding)
- Jina, Cohere (Rerank)
"""
from models.factory import ModelFactory, get_model_factory
from models.base import (
    BaseEmbeddingModel,
    BaseChatModel,
    BaseRerankModel,
)

# Import providers to trigger registration
from models import embeddings  # noqa: F401
from models import llm  # noqa: F401
from models import rerank  # noqa: F401

__all__ = [
    "ModelFactory",
    "get_model_factory",
    "BaseEmbeddingModel",
    "BaseChatModel",
    "BaseRerankModel",
]
