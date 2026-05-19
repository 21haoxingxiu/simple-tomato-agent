"""Embedding model providers."""
from models.embeddings.openai import OpenAIEmbeddingModel
from models.embeddings.zhipuai import ZhipuAIEmbeddingModel
from models.embeddings.dashscope import DashScopeEmbeddingModel
from models.embeddings.ollama import OllamaEmbeddingModel
from models.embeddings.voyage import VoyageEmbeddingModel
from models.embeddings.huggingface import HuggingFaceEmbeddingModel

__all__ = [
    "OpenAIEmbeddingModel",
    "ZhipuAIEmbeddingModel",
    "DashScopeEmbeddingModel",
    "OllamaEmbeddingModel",
    "VoyageEmbeddingModel",
    "HuggingFaceEmbeddingModel",
]
