"""LangGraph chat agent.

Graph: START → router → [retriever(RAG) → generator] / [generator] → END

特性:
- 多路召回(向量 + BM25 + 可选 GraphRAG)、RRF 融合、可选 Cross-Encoder 重排
- 返回 citations,供前端按 [n] 角标定位原文
- 支持流式 token 输出(astream_events)
- LANGCHAIN_TRACING_V2 / LANGCHAIN_API_KEY 自动启用 LangSmith
"""
from __future__ import annotations

import os
import logging
from typing import Annotated, AsyncIterator, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from sqlalchemy.ext.asyncio import AsyncSession

from llm import get_chat_model, is_llm_configured
from rag.pipeline import RetrievedChunk, format_context, get_pipeline

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "你是 AgentStudio 的专业 AI 助手。请根据下面的『参考资料』回答用户问题。\n"
    "要求:\n"
    "1. 优先使用参考资料中的事实,引用资料时在句末标注角标 [1] [2]。\n"
    "2. 若资料与问题无关,可结合自身知识回答,并提醒用户当前知识库未覆盖。\n"
    "3. 回答应结构清晰、专业准确,必要时使用列表/代码块。\n"
    "4. 回答用中文。\n\n"
    "参考资料:\n{context}"
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    workspace_id: str
    kb_id: Optional[str]
    chunks: list[RetrievedChunk]
    db: Optional[AsyncSession]


def _fallback_message(reason: str) -> str:
    return (
        f"[Demo 模式] {reason}\n"
        "已收到你的消息;链路 前端 → Go网关(JWT) → Python LangGraph 正常。\n"
        "请在 agent/.env 中配置真实的 OPENAI_API_KEY 以启用 AI 回复。"
    )


def _build_graph():
    async def router(state: AgentState) -> dict:
        return {"chunks": []}

    async def retriever(state: AgentState) -> dict:
        if not state.get("kb_id") or state.get("db") is None:
            return {"chunks": []}
        last_human = next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            "",
        )
        if not last_human:
            return {"chunks": []}
        try:
            chunks = await get_pipeline().retrieve(
                session=state["db"],
                query=last_human,
                workspace_id=state["workspace_id"],
                kb_id=state["kb_id"],
                top_k=int(os.getenv("RAG_TOP_K", "5")),
                recall_k=int(os.getenv("RAG_RECALL_K", "12")),
            )
        except Exception as exc:
            logger.warning("retrieve failed: %s", exc)
            chunks = []
        return {"chunks": chunks}

    async def generator(state: AgentState) -> dict:
        messages: list[BaseMessage] = []
        ctx = format_context(state.get("chunks") or [])
        if ctx:
            messages.append(SystemMessage(content=SYSTEM_PROMPT.format(context=ctx)))
        messages.extend(state["messages"])

        if not is_llm_configured():
            return {"messages": [AIMessage(content=_fallback_message("未配置 OPENAI_API_KEY"))]}

        try:
            response = await get_chat_model(streaming=True).ainvoke(messages)
            return {"messages": [response]}
        except Exception as exc:
            logger.warning("LLM call failed: %s", exc)
            return {"messages": [AIMessage(content=_fallback_message(f"LLM 调用失败: {exc}"))]}

    def route(state: AgentState) -> str:
        return "retriever" if state.get("kb_id") else "generator"

    g = StateGraph(AgentState)
    g.add_node("router", router)
    g.add_node("retriever", retriever)
    g.add_node("generator", generator)
    g.add_edge(START, "router")
    g.add_conditional_edges("router", route, {"retriever": "retriever", "generator": "generator"})
    g.add_edge("retriever", "generator")
    g.add_edge("generator", END)
    return g.compile()


chat_graph = _build_graph()


def _to_lc(messages: list[dict]) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
        elif role == "system":
            out.append(SystemMessage(content=content))
    return out


async def run_chat(
    messages: list[dict],
    workspace_id: str,
    kb_id: Optional[str],
    db: AsyncSession,
) -> tuple[str, list[RetrievedChunk]]:
    """非流式入口。返回 (assistant_content, citations)"""
    result = await chat_graph.ainvoke(
        {
            "messages": _to_lc(messages),
            "workspace_id": workspace_id,
            "kb_id": kb_id,
            "chunks": [],
            "db": db,
        }
    )
    last = result["messages"][-1]
    content = last.content if hasattr(last, "content") else str(last)
    return content, result.get("chunks") or []


async def stream_chat(
    messages: list[dict],
    workspace_id: str,
    kb_id: Optional[str],
    db: AsyncSession,
) -> AsyncIterator[dict]:
    """流式入口,逐 token yield。

    协议:
      {"event":"retrieved","chunks":[...]}
      {"event":"token","text":"..."}
      {"event":"done","content":"...","chunks":[...]}
      {"event":"error","message":"..."}
    """
    state = {
        "messages": _to_lc(messages),
        "workspace_id": workspace_id,
        "kb_id": kb_id,
        "chunks": [],
        "db": db,
    }

    full_text = ""
    citations: list[RetrievedChunk] = []

    try:
        # stream_mode=["messages","updates"] —— messages 流 token,updates 看 node 输出
        async for stream_mode, payload in chat_graph.astream(
            state, stream_mode=["messages", "updates"]
        ):
            if stream_mode == "updates":
                if not isinstance(payload, dict):
                    continue
                retriever_out = payload.get("retriever")
                if isinstance(retriever_out, dict):
                    chunks = retriever_out.get("chunks") or []
                    if chunks:
                        citations = chunks
                        yield {
                            "event": "retrieved",
                            "chunks": [c.to_dict() for c in citations],
                        }
                continue

            # stream_mode == "messages"
            chunk = payload[0] if isinstance(payload, tuple) else payload
            if chunk is None:
                continue
            token = ""
            if hasattr(chunk, "content"):
                raw = chunk.content
                if isinstance(raw, str):
                    token = raw
                elif isinstance(raw, list):
                    token = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in raw
                    )
            if not token:
                continue
            full_text += token
            yield {"event": "token", "text": token}
    except Exception as exc:
        logger.exception("stream_chat error")
        yield {"event": "error", "message": str(exc)}
        return

    # 兜底:消息流没拿到任何 token 时,再跑一次 ainvoke 取完整内容
    if not full_text:
        try:
            content, _ = await run_chat(messages, workspace_id, kb_id, db)
            if content:
                full_text = content
                yield {"event": "token", "text": content}
        except Exception as exc:
            logger.warning("stream_chat fallback ainvoke failed: %s", exc)

    if not full_text:
        full_text = _fallback_message("LLM 未输出内容")
        yield {"event": "token", "text": full_text}

    yield {
        "event": "done",
        "content": full_text,
        "chunks": [c.to_dict() for c in citations],
    }
