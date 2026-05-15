from __future__ import annotations

import logging

from fastapi import APIRouter, Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Conversation, Message
from schemas.chat import ChatRequest, ChatResponse, ChatMessage
from agents.chat_agent import run_chat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    workspace = x_workspace_id or request.workspace_id
    messages = [m.model_dump() for m in request.messages]

    # Find or create conversation
    conv = Conversation(
        workspace_id=workspace,
        user_id=x_user_id,
        title=messages[0]["content"][:50] if messages else "新会话",
    )
    session.add(conv)

    # Persist user messages
    for m in messages:
        session.add(Message(conversation_id=conv.id, role=m["role"], content=m["content"]))

    content = await run_chat(
        messages=messages,
        workspace_id=workspace,
        kb_id=request.knowledge_base_id,
    )

    # Persist assistant reply
    session.add(Message(conversation_id=conv.id, role="assistant", content=content))
    await session.commit()

    return ChatResponse(
        message=ChatMessage(role="assistant", content=content),
        usage={"workspace_id": workspace, "conversation_id": conv.id},
    )


@router.get("/conversations")
async def list_conversations(
    x_workspace_id: str = Header(default="default"),
    x_user_id: str = Header(default="anonymous"),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Conversation)
        .where(
            Conversation.workspace_id == x_workspace_id,
            Conversation.user_id == x_user_id,
        )
        .order_by(Conversation.created_at.desc())
        .limit(50)
    )
    convs = result.scalars().all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in convs]
