from __future__ import annotations

import json
import logging
import time
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.chat_agent import run_chat, stream_chat
from db.database import AsyncSessionLocal, get_session
from db.models import Conversation, Message
from schemas.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Citation,
    ConversationSummary,
    MessageOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def _resolve_conversation(
    session: AsyncSession,
    conversation_id: Optional[str],
    workspace_id: str,
    user_id: str,
    title: str,
    kb_id: Optional[str],
) -> Conversation:
    if conversation_id:
        conv = await session.get(Conversation, conversation_id)
        if conv and conv.workspace_id == workspace_id and conv.user_id == user_id:
            if kb_id is not None and conv.kb_id != kb_id:
                conv.kb_id = kb_id
            return conv
    conv = Conversation(
        workspace_id=workspace_id,
        user_id=user_id,
        title=title[:80] or "新会话",
        kb_id=kb_id,
    )
    session.add(conv)
    await session.flush()
    return conv


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_workspace_id: str = Header(default="default"),
    session: AsyncSession = Depends(get_session),
):
    workspace = x_workspace_id or request.workspace_id
    messages = [m.model_dump() for m in request.messages]
    if not messages:
        raise HTTPException(400, "messages 不能为空")

    last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
    if not last_user:
        raise HTTPException(400, "未找到用户消息")

    conv = await _resolve_conversation(
        session=session,
        conversation_id=request.conversation_id,
        workspace_id=workspace,
        user_id=x_user_id,
        title=last_user["content"],
        kb_id=request.knowledge_base_id,
    )

    session.add(Message(conversation_id=conv.id, role=last_user["role"], content=last_user["content"]))

    started = time.time()
    content, citations = await run_chat(
        messages=messages,
        workspace_id=workspace,
        kb_id=request.knowledge_base_id,
        db=session,
    )
    latency = int((time.time() - started) * 1000)

    citations_payload = [c.to_dict() for c in citations]
    session.add(
        Message(
            conversation_id=conv.id,
            role="assistant",
            content=content,
            citations=citations_payload,
            latency_ms=latency,
        )
    )
    await session.commit()

    return ChatResponse(
        conversation_id=conv.id,
        message=ChatMessage(role="assistant", content=content),
        citations=[Citation(**c) for c in citations_payload],
        usage={
            "workspace_id": workspace,
            "kb_id": request.knowledge_base_id or "",
            "latency_ms": latency,
        },
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_workspace_id: str = Header(default="default"),
):
    """SSE 流式输出 — 与 Go 网关 stream 透传配合。"""
    workspace = x_workspace_id or request.workspace_id
    messages = [m.model_dump() for m in request.messages]
    if not messages:
        raise HTTPException(400, "messages 不能为空")

    last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
    if not last_user:
        raise HTTPException(400, "未找到用户消息")

    async def event_stream() -> AsyncIterator[bytes]:
        async with AsyncSessionLocal() as session:
            conv = await _resolve_conversation(
                session=session,
                conversation_id=request.conversation_id,
                workspace_id=workspace,
                user_id=x_user_id,
                title=last_user["content"],
                kb_id=request.knowledge_base_id,
            )
            session.add(
                Message(conversation_id=conv.id, role=last_user["role"], content=last_user["content"])
            )
            await session.flush()
            yield _sse({"event": "conversation", "conversation_id": conv.id})

            started = time.time()
            final_content = ""
            citations: list[dict] = []
            error_msg: Optional[str] = None
            try:
                async for evt in stream_chat(
                    messages=messages,
                    workspace_id=workspace,
                    kb_id=request.knowledge_base_id,
                    db=session,
                ):
                    if evt.get("event") == "retrieved":
                        citations = evt.get("chunks", [])
                    elif evt.get("event") == "done":
                        final_content = evt.get("content", "")
                        citations = evt.get("chunks", citations)
                    elif evt.get("event") == "error":
                        error_msg = evt.get("message")
                    yield _sse(evt)
            except Exception as exc:
                logger.exception("stream error")
                error_msg = str(exc)
                yield _sse({"event": "error", "message": error_msg})

            latency = int((time.time() - started) * 1000)
            if final_content or error_msg:
                session.add(
                    Message(
                        conversation_id=conv.id,
                        role="assistant",
                        content=final_content or f"[error] {error_msg}",
                        citations=citations,
                        latency_ms=latency,
                    )
                )
            await session.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    x_workspace_id: str = Header(default="default"),
    x_user_id: str = Header(default="anonymous"),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(
        select(
            Conversation,
            func.count(Message.id).label("msg_count"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(
            Conversation.workspace_id == x_workspace_id,
            Conversation.user_id == x_user_id,
        )
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
        .limit(100)
    )
    out = []
    for conv, msg_count in res.all():
        out.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                kb_id=conv.kb_id,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                message_count=int(msg_count or 0),
            )
        )
    return out


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageOut])
async def get_conversation_messages(
    conv_id: str,
    x_workspace_id: str = Header(default="default"),
    x_user_id: str = Header(default="anonymous"),
    session: AsyncSession = Depends(get_session),
):
    conv = await session.get(Conversation, conv_id)
    if not conv or conv.workspace_id != x_workspace_id or conv.user_id != x_user_id:
        raise HTTPException(404, "Conversation not found")
    res = await session.execute(
        select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at.asc())
    )
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            created_at=m.created_at.isoformat(),
        )
        for m in res.scalars().all()
    ]


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: str,
    x_workspace_id: str = Header(default="default"),
    x_user_id: str = Header(default="anonymous"),
    session: AsyncSession = Depends(get_session),
):
    conv = await session.get(Conversation, conv_id)
    if not conv or conv.workspace_id != x_workspace_id or conv.user_id != x_user_id:
        raise HTTPException(404, "Conversation not found")
    await session.execute(sa_delete(Message).where(Message.conversation_id == conv_id))
    await session.delete(conv)
    await session.commit()
    return {"ok": True, "deleted_id": conv_id}
