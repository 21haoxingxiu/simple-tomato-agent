"""RAG 主流水线:
- ingest: 解析 -> 切片 -> 落 SQL chunks -> 向量入库 -> BM25 入库 -> (可选) Graph 入库
- retrieve: 多路召回(向量 + BM25) -> RRF 融合 -> (可选) CrossEncoder 重排 -> 返回 RetrievedChunk
"""
from __future__ import annotations

import os
import uuid
import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Chunk, Document
from rag.bm25 import get_bm25
from rag.reranker import is_cross_encoder_enabled, rerank_cross_encoder, rrf_fuse
from rag.splitter import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    estimate_tokens,
    parse_file,
    split_text,
)
from rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_id: str = ""
    filename: str = ""
    rerank_score: Optional[float] = None
    sources: list[str] = field(default_factory=list)  # ["vector","bm25","graph"]

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "score": round(self.score, 4),
            "document_id": self.document_id,
            "filename": self.filename,
            "rerank_score": (
                round(self.rerank_score, 4) if self.rerank_score is not None else None
            ),
            "sources": self.sources,
        }


class RAGPipeline:
    def __init__(self) -> None:
        self.vector_store = get_vector_store()
        self.bm25 = get_bm25()
        self.graph_enabled = os.getenv("ENABLE_GRAPHRAG", "false").lower() == "true"

    # ---------------- ingest ----------------

    async def ingest_document(
        self,
        session: AsyncSession,
        document: Document,
        workspace_id: str,
        raw_bytes: bytes,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> int:
        text = parse_file(document.filename, raw_bytes)
        if not text.strip():
            raise ValueError("文档解析后为空,无法入库")

        pieces = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not pieces:
            raise ValueError("分块结果为空")

        chunks_for_store: list[dict] = []
        chunk_rows: list[Chunk] = []

        for seq, piece in enumerate(pieces):
            cid = str(uuid.uuid4())
            metadata = {
                "chunk_id": cid,
                "document_id": document.id,
                "kb_id": document.kb_id,
                "workspace_id": workspace_id,
                "filename": document.filename,
                "seq": seq,
            }
            chunks_for_store.append({"id": cid, "content": piece, "metadata": metadata})
            chunk_rows.append(
                Chunk(
                    id=cid,
                    document_id=document.id,
                    kb_id=document.kb_id,
                    workspace_id=workspace_id,
                    seq=seq,
                    content=piece,
                    tokens=estimate_tokens(piece),
                    vector_id=cid,
                    extra_meta={"filename": document.filename},
                )
            )

        # 1. SQL
        session.add_all(chunk_rows)

        # 2. 向量
        try:
            self.vector_store.add_chunks(document.kb_id, workspace_id, chunks_for_store)
        except Exception as exc:
            logger.exception("vector ingest failed")
            raise RuntimeError(f"向量索引失败: {exc}") from exc

        # 3. BM25
        try:
            self.bm25.add_chunks(document.kb_id, workspace_id, chunks_for_store)
        except Exception as exc:
            logger.warning("bm25 ingest failed: %s (continue)", exc)

        # 4. Graph(可选)
        if self.graph_enabled:
            try:
                from graph.graphrag import get_graph_store

                gs = get_graph_store()
                if gs is not None:
                    await gs.ingest_chunks(workspace_id, document.kb_id, chunks_for_store)
            except Exception as exc:
                logger.warning("graph ingest skipped: %s", exc)

        return len(chunks_for_store)

    async def delete_document(
        self, session: AsyncSession, workspace_id: str, kb_id: str, document_id: str
    ) -> None:
        try:
            self.vector_store.delete_by_document(kb_id, workspace_id, document_id)
        except Exception as exc:
            logger.warning("vector delete failed: %s", exc)
        try:
            self.bm25.delete_by_document(kb_id, workspace_id, document_id)
        except Exception as exc:
            logger.warning("bm25 delete failed: %s", exc)

    # ---------------- retrieve ----------------

    async def retrieve(
        self,
        session: AsyncSession,
        query: str,
        workspace_id: str,
        kb_id: str,
        top_k: int = 5,
        recall_k: int = 12,
        use_rerank: Optional[bool] = None,
    ) -> list[RetrievedChunk]:
        """多路召回 -> RRF -> 重排 -> 取 top_k。"""
        if use_rerank is None:
            use_rerank = is_cross_encoder_enabled()

        # 向量召回
        vec_hits: list[tuple[str, float, dict]] = []
        try:
            for doc, score in self.vector_store.similarity_search(
                kb_id, workspace_id, query, k=recall_k
            ):
                cid = doc.metadata.get("chunk_id")
                if not cid:
                    continue
                vec_hits.append((cid, float(score), {**doc.metadata, "content": doc.page_content}))
        except Exception as exc:
            logger.warning("vector retrieve failed: %s", exc)

        # BM25 召回
        bm25_hits: list[tuple[str, float, dict]] = []
        try:
            bm25_hits = self.bm25.search(kb_id, workspace_id, query, k=recall_k)
        except Exception as exc:
            logger.warning("bm25 retrieve failed: %s", exc)

        # Graph 召回(可选,作为额外路径)
        graph_hits: list[tuple[str, float, dict]] = []
        if self.graph_enabled:
            try:
                from graph.graphrag import get_graph_store

                gs = get_graph_store()
                if gs is not None:
                    graph_hits = await gs.search(workspace_id, kb_id, query, k=recall_k)
            except Exception as exc:
                logger.warning("graph retrieve skipped: %s", exc)

        # 汇总元数据(BM25 / Vector / Graph 同一 cid 合并)
        meta_pool: dict[str, dict] = {}
        sources_pool: dict[str, set[str]] = {}
        score_pool: dict[str, float] = {}

        def _absorb(name: str, hits: list[tuple[str, float, dict]]) -> list[str]:
            ranked_ids: list[str] = []
            for cid, score, meta in hits:
                ranked_ids.append(cid)
                meta_pool.setdefault(cid, meta)
                sources_pool.setdefault(cid, set()).add(name)
                score_pool[cid] = max(score_pool.get(cid, 0.0), float(score))
            return ranked_ids

        rankings: list[list[str]] = []
        if vec_hits:
            rankings.append(_absorb("vector", vec_hits))
        if bm25_hits:
            rankings.append(_absorb("bm25", bm25_hits))
        if graph_hits:
            rankings.append(_absorb("graph", graph_hits))

        if not rankings:
            return []

        fused = rrf_fuse(rankings, top_k=max(recall_k, top_k))

        # 用 SQL chunks 表回填缺失字段(content/filename)以保证一致
        cids = [cid for cid, _ in fused]
        if cids:
            stmt = select(Chunk).where(Chunk.id.in_(cids))
            rows = (await session.execute(stmt)).scalars().all()
            chunk_map = {c.id: c for c in rows}
        else:
            chunk_map = {}

        candidates: list[dict] = []
        for cid, fused_score in fused:
            meta = meta_pool.get(cid, {})
            chunk_row = chunk_map.get(cid)
            content = (
                meta.get("content")
                or (chunk_row.content if chunk_row else "")
                or ""
            )
            filename = (
                meta.get("filename")
                or (chunk_row.extra_meta.get("filename") if chunk_row else "")
                or ""
            )
            document_id = meta.get("document_id") or (chunk_row.document_id if chunk_row else "")
            candidates.append(
                {
                    "chunk_id": cid,
                    "content": content,
                    "filename": filename,
                    "document_id": document_id,
                    "score": float(fused_score),
                    "sources": sorted(sources_pool.get(cid, set())),
                }
            )

        # 重排
        if use_rerank and candidates:
            candidates = rerank_cross_encoder(query, candidates, top_k=top_k)
        else:
            candidates = candidates[:top_k]

        return [
            RetrievedChunk(
                chunk_id=c["chunk_id"],
                content=c["content"],
                score=c["score"],
                document_id=c["document_id"],
                filename=c["filename"],
                rerank_score=c.get("rerank_score"),
                sources=c["sources"],
            )
            for c in candidates
        ]


_pipeline: Optional[RAGPipeline] = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


def format_context(chunks: list[RetrievedChunk]) -> str:
    """将检索结果格式化为可注入 system prompt 的字符串,带角标用于引用。"""
    if not chunks:
        return ""
    parts = []
    for i, c in enumerate(chunks, 1):
        src = f" 来源:{c.filename}" if c.filename else ""
        parts.append(f"[{i}]{src}\n{c.content}")
    return "\n\n".join(parts)
