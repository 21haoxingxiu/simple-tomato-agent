from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class Citation(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_id: str = ""
    filename: str = ""
    rerank_score: Optional[float] = None
    sources: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    workspace_id: str = "default"
    conversation_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessage
    citations: list[Citation] = Field(default_factory=list)
    usage: dict = Field(default_factory=dict)


class ConversationSummary(BaseModel):
    id: str
    title: str
    kb_id: Optional[str] = None
    created_at: str
    updated_at: str
    message_count: int = 0


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    citations: list[dict] = Field(default_factory=list)
    created_at: str
