"""BM25 倒排检索:
- 默认 rank_bm25 内存索引,按 (workspace_id, kb_id) 分桶
- 启用 ES_URL 时使用 Elasticsearch BM25,落盘可扩展
- 中文使用 jieba 分词,缺失时回退 char-level n-gram
"""
from __future__ import annotations

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    import jieba

    _HAS_JIEBA = True
except Exception:  # pragma: no cover
    _HAS_JIEBA = False


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    if _HAS_JIEBA and any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return [t for t in jieba.lcut(text) if t.strip()]
    return _TOKEN_RE.findall(text)


class BaseBM25(ABC):
    @abstractmethod
    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> int:
        ...

    @abstractmethod
    def search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[str, float, dict]]:
        """返回 [(chunk_id, score, metadata)]"""

    @abstractmethod
    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        ...


class InMemoryBM25(BaseBM25):
    """内存版 BM25,按 namespace 分组;重启丢失,适合单机/Demo。"""

    def __init__(self) -> None:
        self._bucket: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _ns(workspace_id: str, kb_id: str) -> str:
        return f"{workspace_id}::{kb_id}"

    def _ensure(self, ns: str) -> dict[str, Any]:
        if ns not in self._bucket:
            self._bucket[ns] = {"chunk_ids": [], "tokens": [], "metas": [], "model": None}
        return self._bucket[ns]

    def _rebuild(self, ns: str) -> None:
        from rank_bm25 import BM25Okapi

        b = self._bucket.get(ns)
        if not b or not b["tokens"]:
            if b is not None:
                b["model"] = None
            return
        b["model"] = BM25Okapi(b["tokens"])

    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> int:
        ns = self._ns(workspace_id, kb_id)
        b = self._ensure(ns)
        for c in chunks:
            b["chunk_ids"].append(c["id"])
            b["tokens"].append(tokenize(c["content"]))
            meta = {**c.get("metadata", {}), "content": c["content"]}
            b["metas"].append(meta)
        self._rebuild(ns)
        return len(chunks)

    def search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[str, float, dict]]:
        ns = self._ns(workspace_id, kb_id)
        b = self._bucket.get(ns)
        if not b or b["model"] is None:
            return []
        scores = b["model"].get_scores(tokenize(query))
        if scores is None or len(scores) == 0:
            return []
        max_score = float(max(scores)) or 1.0
        idxs = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [
            (b["chunk_ids"][i], float(scores[i]) / max_score, b["metas"][i])
            for i in idxs
            if scores[i] > 0
        ]

    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        ns = self._ns(workspace_id, kb_id)
        b = self._bucket.get(ns)
        if not b:
            return 0
        keep_ids, keep_toks, keep_metas = [], [], []
        removed = 0
        for cid, tok, meta in zip(b["chunk_ids"], b["tokens"], b["metas"]):
            if meta.get("document_id") == document_id:
                removed += 1
                continue
            keep_ids.append(cid)
            keep_toks.append(tok)
            keep_metas.append(meta)
        b["chunk_ids"], b["tokens"], b["metas"] = keep_ids, keep_toks, keep_metas
        self._rebuild(ns)
        return removed


class ElasticsearchBM25(BaseBM25):
    """ES 适配器。通过 ES_URL 启用。"""

    def __init__(self) -> None:
        from elasticsearch import Elasticsearch  # type: ignore

        self.url = os.getenv("ES_URL", "http://localhost:9200")
        self.client = Elasticsearch(self.url)
        self.prefix = os.getenv("ES_INDEX_PREFIX", "ai_demo_kb_")

    def _index(self, workspace_id: str, kb_id: str) -> str:
        return f"{self.prefix}{workspace_id}_{kb_id}".replace("-", "_").lower()

    def _ensure_index(self, idx: str) -> None:
        if self.client.indices.exists(index=idx):
            return
        self.client.indices.create(
            index=idx,
            body={
                "mappings": {
                    "properties": {
                        "chunk_id": {"type": "keyword"},
                        "content": {"type": "text", "analyzer": "standard"},
                        "document_id": {"type": "keyword"},
                        "metadata": {"type": "object", "enabled": True},
                    }
                }
            },
            ignore=400,
        )

    def add_chunks(self, kb_id: str, workspace_id: str, chunks: list[dict]) -> int:
        from elasticsearch.helpers import bulk  # type: ignore

        idx = self._index(workspace_id, kb_id)
        self._ensure_index(idx)
        actions = [
            {
                "_index": idx,
                "_id": c["id"],
                "_source": {
                    "chunk_id": c["id"],
                    "content": c["content"],
                    "document_id": c.get("metadata", {}).get("document_id", ""),
                    "metadata": c.get("metadata", {}),
                },
            }
            for c in chunks
        ]
        bulk(self.client, actions)
        return len(chunks)

    def search(
        self, kb_id: str, workspace_id: str, query: str, k: int = 8
    ) -> list[tuple[str, float, dict]]:
        idx = self._index(workspace_id, kb_id)
        try:
            res = self.client.search(
                index=idx,
                body={"query": {"match": {"content": query}}, "size": k},
            )
        except Exception as exc:
            logger.warning("ES search failed: %s", exc)
            return []
        hits = res.get("hits", {}).get("hits", [])
        if not hits:
            return []
        max_score = max(h["_score"] for h in hits) or 1.0
        return [
            (
                h["_source"]["chunk_id"],
                float(h["_score"]) / max_score,
                {**h["_source"].get("metadata", {}), "content": h["_source"]["content"]},
            )
            for h in hits
        ]

    def delete_by_document(self, kb_id: str, workspace_id: str, document_id: str) -> int:
        idx = self._index(workspace_id, kb_id)
        try:
            res = self.client.delete_by_query(
                index=idx, body={"query": {"term": {"document_id": document_id}}}
            )
            return int(res.get("deleted", 0))
        except Exception as exc:
            logger.warning("ES delete failed: %s", exc)
            return 0


_singleton: Optional[BaseBM25] = None


def get_bm25() -> BaseBM25:
    global _singleton
    if _singleton is not None:
        return _singleton
    backend = os.getenv("BM25_BACKEND", "memory").lower()
    if backend == "elasticsearch" and os.getenv("ES_URL"):
        try:
            _singleton = ElasticsearchBM25()
            logger.info("BM25 backend=Elasticsearch")
            return _singleton
        except Exception as exc:
            logger.warning("ES init failed (%s) — falling back to memory BM25", exc)
    _singleton = InMemoryBM25()
    logger.info("BM25 backend=InMemory")
    return _singleton
