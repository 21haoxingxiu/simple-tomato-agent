from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class KBCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    config: dict = Field(default_factory=dict)


class KBUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None


class KBResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: str
    doc_count: int
    chunk_count: int
    status: str
    config: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str


class DocumentResponse(BaseModel):
    id: str
    kb_id: str
    filename: str
    mime_type: str = ""
    size_bytes: int = 0
    chunk_count: int = 0
    status: str
    error_msg: str = ""
    created_at: str


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5
    recall_k: int = 12
    use_rerank: Optional[bool] = None


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_id: str = ""
    filename: str = ""
    rerank_score: Optional[float] = None
    sources: list[str] = Field(default_factory=list)
