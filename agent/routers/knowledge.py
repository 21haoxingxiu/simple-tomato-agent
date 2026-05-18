from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Chunk, Document, KnowledgeBase
from rag.pipeline import get_pipeline
from rag.splitter import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from schemas.knowledge import (
    DocumentResponse,
    KBCreate,
    KBResponse,
    KBUpdate,
    RetrievedChunkOut,
    RetrieveRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _kb_to_response(kb: KnowledgeBase) -> dict:
    return {
        "id": kb.id,
        "workspace_id": kb.workspace_id,
        "name": kb.name,
        "description": kb.description,
        "doc_count": kb.doc_count,
        "chunk_count": kb.chunk_count,
        "status": kb.status,
        "config": kb.config or {},
        "created_at": kb.created_at.isoformat(),
        "updated_at": kb.updated_at.isoformat(),
    }


def _doc_to_response(doc: Document) -> dict:
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "filename": doc.filename,
        "mime_type": doc.mime_type,
        "size_bytes": doc.size_bytes,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "error_msg": doc.error_msg,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/bases", response_model=list[KBResponse])
async def list_bases(
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.workspace_id == x_workspace_id)
        .order_by(KnowledgeBase.created_at.desc())
    )
    return [_kb_to_response(kb) for kb in res.scalars().all()]


@router.post("/bases", response_model=KBResponse)
async def create_base(
    body: KBCreate,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = KnowledgeBase(
        workspace_id=x_workspace_id,
        name=body.name,
        description=body.description or "",
        config=body.config or {},
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return _kb_to_response(kb)


@router.get("/bases/{kb_id}", response_model=KBResponse)
async def get_base(
    kb_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    return _kb_to_response(kb)


@router.patch("/bases/{kb_id}", response_model=KBResponse)
async def update_base(
    kb_id: str,
    body: KBUpdate,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    if body.name is not None:
        kb.name = body.name
    if body.description is not None:
        kb.description = body.description
    if body.config is not None:
        kb.config = body.config
    await session.commit()
    await session.refresh(kb)
    return _kb_to_response(kb)


@router.delete("/bases/{kb_id}")
async def delete_base(
    kb_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    # 删除向量库 & BM25
    docs = (
        await session.execute(select(Document).where(Document.kb_id == kb_id))
    ).scalars().all()
    pipeline = get_pipeline()
    for d in docs:
        await pipeline.delete_document(session, x_workspace_id, kb_id, d.id)
    await session.delete(kb)
    await session.commit()
    return {"ok": True, "deleted_id": kb_id}


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentResponse])
async def list_documents(
    kb_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    res = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return [_doc_to_response(d) for d in res.scalars().all()]


@router.post("/bases/{kb_id}/upload", response_model=DocumentResponse)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    chunk_size: int = Form(DEFAULT_CHUNK_SIZE),
    chunk_overlap: int = Form(DEFAULT_CHUNK_OVERLAP),
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")

    content = await file.read()
    doc = Document(
        kb_id=kb_id,
        filename=file.filename or "unknown",
        mime_type=file.content_type or "",
        size_bytes=len(content),
        status="parsing",
    )
    session.add(doc)
    kb.status = "indexing"
    await session.commit()
    await session.refresh(doc)

    try:
        pipeline = get_pipeline()
        chunk_count = await pipeline.ingest_document(
            session=session,
            document=doc,
            workspace_id=x_workspace_id,
            raw_bytes=content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        doc.chunk_count = chunk_count
        doc.status = "ready"
        kb.doc_count = (kb.doc_count or 0) + 1
        kb.chunk_count = (kb.chunk_count or 0) + chunk_count
        kb.status = "ready"
        await session.commit()
        await session.refresh(doc)
        return _doc_to_response(doc)
    except Exception as exc:
        logger.exception("upload_document failed")
        doc.status = "error"
        doc.error_msg = str(exc)[:1000]
        kb.status = "ready"
        await session.commit()
        raise HTTPException(500, detail=str(exc))


@router.delete("/bases/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: str,
    doc_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    doc = await session.get(Document, doc_id)
    if not doc or doc.kb_id != kb_id:
        raise HTTPException(404, "Document not found")

    pipeline = get_pipeline()
    await pipeline.delete_document(session, x_workspace_id, kb_id, doc_id)

    # 删除 chunks
    await session.execute(sa_delete(Chunk).where(Chunk.document_id == doc_id))
    removed_chunks = doc.chunk_count
    await session.delete(doc)
    kb.doc_count = max(0, (kb.doc_count or 1) - 1)
    kb.chunk_count = max(0, (kb.chunk_count or removed_chunks) - removed_chunks)
    await session.commit()
    return {"ok": True, "deleted_id": doc_id}


@router.post("/bases/{kb_id}/retrieve", response_model=list[RetrievedChunkOut])
async def retrieve_debug(
    kb_id: str,
    body: RetrieveRequest,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    """检索调试接口:命中片段一目了然,便于评估召回质量。"""
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    chunks = await get_pipeline().retrieve(
        session=session,
        query=body.query,
        workspace_id=x_workspace_id,
        kb_id=kb_id,
        top_k=body.top_k,
        recall_k=body.recall_k,
        use_rerank=body.use_rerank,
    )
    return [c.to_dict() for c in chunks]


@router.get("/bases/{kb_id}/stats")
async def kb_stats(
    kb_id: str,
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(404, "Knowledge base not found")
    chunk_count = (
        await session.execute(select(func.count(Chunk.id)).where(Chunk.kb_id == kb_id))
    ).scalar() or 0
    doc_count = (
        await session.execute(select(func.count(Document.id)).where(Document.kb_id == kb_id))
    ).scalar() or 0
    return {
        "id": kb.id,
        "name": kb.name,
        "doc_count": doc_count,
        "chunk_count": chunk_count,
        "status": kb.status,
    }
