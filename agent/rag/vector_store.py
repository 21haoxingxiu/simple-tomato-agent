"""向量库适配层:
- 默认 Chroma 本地;通过 VECTOR_STORE=milvus 切换至 Milvus
- 统一 add_chunks / search 接口供 RAGPipeline 调用
"""
from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from langchain_core.documents import Document

from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    @abstractmethod
    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> list[str]:
        """chunks: [{id, content, metadata}]  -> 返回 vector_ids"""

    @abstractmethod
    def similarity_search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        """返回 [(doc, score)] score 越大越相关 (0..1)"""

    @abstractmethod
    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        """按 document_id 删除"""


def _collection_name(workspace_id: str, kb_id: str) -> str:
    """Chroma 限制 collection 名 3-63 字符,且仅允许 [A-Za-z0-9_-]。
    workspace_id/kb_id 是 UUID(36 字符),拼接后会超长 + 含 '-' 实际允许但太长。
    用 sha1 哈希前 24 位 + 短前缀,确定性且短。
    """
    import hashlib

    raw = f"{workspace_id}::{kb_id}"
    digest = hashlib.sha1(raw.encode()).hexdigest()[:24]
    return f"kb_{digest}"


class ChromaVectorStore(BaseVectorStore):
    def __init__(self) -> None:
        self.persist_dir = os.getenv("CHROMA_DIR", "./data/chroma")
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)

    def _vs(self, kb_id: str, workspace_id: str):
        from langchain_chroma import Chroma

        return Chroma(
            collection_name=_collection_name(workspace_id, kb_id),
            embedding_function=get_embeddings(),
            persist_directory=self.persist_dir,
        )

    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> list[str]:
        vs = self._vs(kb_id, workspace_id)
        docs = [
            Document(page_content=c["content"], metadata={**c.get("metadata", {}), "chunk_id": c["id"]})
            for c in chunks
        ]
        ids = [c["id"] for c in chunks]
        vs.add_documents(documents=docs, ids=ids)
        return ids

    def similarity_search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        vs = self._vs(kb_id, workspace_id)
        try:
            pairs = vs.similarity_search_with_relevance_scores(query, k=k)
            return pairs
        except Exception as exc:
            logger.warning("relevance_scores failed (%s), falling back to plain search", exc)
            docs = vs.similarity_search(query, k=k)
            return [(d, 0.5) for d in docs]

    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        vs = self._vs(kb_id, workspace_id)
        try:
            vs.delete(where={"document_id": document_id})
        except Exception as exc:
            logger.warning("Chroma delete failed: %s", exc)
            return 0
        return 1


class MilvusVectorStore(BaseVectorStore):
    """可选 Milvus 实现。需要 langchain-milvus + pymilvus。

    通过环境变量 MILVUS_URI 例如 http://localhost:19530 启用。
    """

    def __init__(self) -> None:
        self.uri = os.getenv("MILVUS_URI", "http://localhost:19530")
        self.token = os.getenv("MILVUS_TOKEN", "")

    def _vs(self, kb_id: str, workspace_id: str):
        from langchain_milvus import Milvus  # type: ignore

        connection_args: dict[str, Any] = {"uri": self.uri}
        if self.token:
            connection_args["token"] = self.token
        return Milvus(
            embedding_function=get_embeddings(),
            collection_name=_collection_name(workspace_id, kb_id),
            connection_args=connection_args,
            auto_id=False,
        )

    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> list[str]:
        vs = self._vs(kb_id, workspace_id)
        docs = [
            Document(page_content=c["content"], metadata={**c.get("metadata", {}), "chunk_id": c["id"]})
            for c in chunks
        ]
        ids = [c["id"] for c in chunks]
        vs.add_documents(documents=docs, ids=ids)
        return ids

    def similarity_search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        vs = self._vs(kb_id, workspace_id)
        try:
            return vs.similarity_search_with_relevance_scores(query, k=k)
        except Exception:
            docs = vs.similarity_search(query, k=k)
            return [(d, 0.5) for d in docs]

    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        vs = self._vs(kb_id, workspace_id)
        try:
            expr = f'document_id == "{document_id}"'
            vs.delete(expr=expr)
            return 1
        except Exception as exc:
            logger.warning("Milvus delete failed: %s", exc)
            return 0


_singleton: Optional[BaseVectorStore] = None


def get_vector_store() -> BaseVectorStore:
    global _singleton
    if _singleton is not None:
        return _singleton
    backend = os.getenv("VECTOR_STORE", "chroma").lower()
    if backend == "milvus":
        try:
            _singleton = MilvusVectorStore()
            logger.info("VectorStore=Milvus")
            return _singleton
        except Exception as exc:
            logger.warning("Milvus init failed (%s) — falling back to Chroma", exc)
    _singleton = ChromaVectorStore()
    logger.info("VectorStore=Chroma persist_dir=%s", _singleton.persist_dir)
    return _singleton
