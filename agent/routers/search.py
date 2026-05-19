"""Search API router for global search across knowledge bases, conversations, documents."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import KnowledgeBase, Conversation, Document, Message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class KnowledgeBaseResult(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    doc_count: int = 0


class ConversationResult(BaseModel):
    id: str
    title: Optional[str] = None
    last_message: Optional[str] = None


class DocumentResult(BaseModel):
    id: str
    kb_id: str
    filename: str
    status: str


class SearchResult(BaseModel):
    knowledge_bases: list[KnowledgeBaseResult] = []
    conversations: list[ConversationResult] = []
    documents: list[DocumentResult] = []


@router.get("", response_model=SearchResult)
async def global_search(
    q: str,
    x_workspace_id: str = Header(..., alias="X-Workspace-ID"),
    session: AsyncSession = Depends(get_session),
):
    """Global search across knowledge bases, conversations, and documents."""
    query = f"%{q}%"
    workspace_id = x_workspace_id  # UUID string, not int

    # Search knowledge bases
    kb_stmt = select(KnowledgeBase).where(
        KnowledgeBase.workspace_id == workspace_id,
        or_(
            KnowledgeBase.name.ilike(query),
            KnowledgeBase.description.ilike(query),
        ),
    ).limit(5)
    kb_result = await session.execute(kb_stmt)
    knowledge_bases = [
        KnowledgeBaseResult(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            doc_count=kb.doc_count,
        )
        for kb in kb_result.scalars()
    ]

    # Search conversations
    conv_stmt = (
        select(Conversation)
        .where(
            Conversation.workspace_id == workspace_id,
            or_(
                Conversation.title.ilike(query),
                Conversation.id.in_(
                    select(Message.conversation_id).where(
                        Message.content.ilike(query)
                    )
                ),
            ),
        )
        .limit(5)
    )
    conv_result = await session.execute(conv_stmt)
    conversations = []
    for conv in conv_result.scalars():
        # Get last message
        last_msg_stmt = select(Message).where(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).limit(1)
        last_msg_result = await session.execute(last_msg_stmt)
        last_msg = last_msg_result.scalar_one_or_none()
        conversations.append(
            ConversationResult(
                id=str(conv.id),
                title=conv.title,
                last_message=last_msg.content[:100] if last_msg and last_msg.content else None,
            )
        )

    # Search documents
    doc_stmt = (
        select(Document)
        .join(KnowledgeBase, Document.kb_id == KnowledgeBase.id)
        .where(
            KnowledgeBase.workspace_id == workspace_id,
            or_(
                Document.filename.ilike(query),
                Document.error_msg.ilike(query),
            ),
        )
        .limit(5)
    )
    doc_result = await session.execute(doc_stmt)
    documents = [
        DocumentResult(
            id=str(doc.id),
            kb_id=str(doc.kb_id),
            filename=doc.filename,
            status=doc.status,
        )
        for doc in doc_result.scalars()
    ]

    return SearchResult(
        knowledge_bases=knowledge_bases,
        conversations=conversations,
        documents=documents,
    )
