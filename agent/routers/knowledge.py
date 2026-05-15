from __future__ import annotations

import io
import logging
from typing import Optional

from fastapi import APIRouter, Header, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import KnowledgeBase, Document
from agents.rag_service import ingest_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KBCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class KBResponse(BaseModel):
    id: str
    name: str
    description: str
    doc_count: int
    status: str
    workspace_id: str

    class Config:
        from_attributes = True


@router.get("/bases", response_model=list[KBResponse])
async def list_bases(
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(KnowledgeBase).where(KnowledgeBase.workspace_id == x_workspace_id)
    )
    return result.scalars().all()


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
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


@router.post("/bases/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    kb = await session.get(KnowledgeBase, kb_id)
    if not kb or kb.workspace_id != x_workspace_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    content = await file.read()
    text = ""

    if file.filename and file.filename.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"PDF parse error: {exc}")
    else:
        text = content.decode("utf-8", errors="replace")

    kb.status = "indexing"
    await session.commit()

    try:
        chunk_count = await ingest_text(
            text=text,
            workspace_id=x_workspace_id,
            kb_id=kb_id,
            metadata={"filename": file.filename},
        )
        doc = Document(kb_id=kb_id, filename=file.filename or "unknown", chunk_count=chunk_count)
        session.add(doc)
        kb.doc_count += 1
        kb.status = "ready"
        await session.commit()
        return {"kb_id": kb_id, "filename": file.filename, "chunks": chunk_count}
    except Exception as exc:
        kb.status = "error"
        await session.commit()
        raise HTTPException(status_code=500, detail=str(exc))
