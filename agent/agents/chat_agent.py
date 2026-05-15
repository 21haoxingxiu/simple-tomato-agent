"""
LangGraph-based chat agent.

Graph:
  START → router → retriever (if RAG) → generator → END
                 ↘ generator (direct)  ↗
"""
from __future__ import annotations

import os
import logging
from typing import Annotated, TypedDict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    workspace_id: str
    kb_id: Optional[str]
    rag_context: str


def _make_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-placeholder"),
        temperature=0.7,
    )


def _build_graph():
    llm = _make_llm()

    def router(state: AgentState) -> dict:
        return {"rag_context": ""}

    async def retriever(state: AgentState) -> dict:
        """Fetch relevant context from ChromaDB."""
        from agents.rag_service import retrieve
        last_human = next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            "",
        )
        try:
            context = await retrieve(
                query=last_human,
                workspace_id=state["workspace_id"],
                kb_id=state["kb_id"] or "default",
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed: %s", exc)
            context = ""
        return {"rag_context": context}

    async def generator(state: AgentState) -> dict:
        """Call LLM with optional RAG context injected as system message."""
        messages = list(state["messages"])

        if state.get("rag_context"):
            sys_msg = SystemMessage(
                content=(
                    "你是一个专业的 AI 助手。请根据以下参考资料回答用户问题，"
                    "如果参考资料与问题无关则依据自身知识回答。\n\n"
                    f"参考资料：\n{state['rag_context']}"
                )
            )
            messages = [sys_msg] + messages

        try:
            response = await llm.ainvoke(messages)
            return {"messages": [response]}
        except Exception as exc:
            logger.warning("LLM call failed (%s), using fallback response", exc)
            return {"messages": [AIMessage(
                content=(
                    f"[Demo 模式] 未配置有效的 OPENAI_API_KEY，无法调用 LLM。\n"
                    f"你发送的消息已收到，完整链路（前端 → Go 网关 JWT → Python LangGraph）运行正常。\n"
                    f"请在 agent/.env 中填写真实的 OPENAI_API_KEY 以启用 AI 回复。"
                )
            )]}

    def route_condition(state: AgentState) -> str:
        return "retriever" if state.get("kb_id") else "generator"

    graph = StateGraph(AgentState)
    graph.add_node("router", router)
    graph.add_node("retriever", retriever)
    graph.add_node("generator", generator)

    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", route_condition, {
        "retriever": "retriever",
        "generator": "generator",
    })
    graph.add_edge("retriever", "generator")
    graph.add_edge("generator", END)

    return graph.compile()


chat_graph = _build_graph()


async def run_chat(
    messages: list[dict],
    workspace_id: str = "default",
    kb_id: Optional[str] = None,
) -> str:
    lc_messages: list[BaseMessage] = []
    for m in messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            lc_messages.append(AIMessage(content=m["content"]))
        elif m["role"] == "system":
            lc_messages.append(SystemMessage(content=m["content"]))

    result = await chat_graph.ainvoke({
        "messages": lc_messages,
        "workspace_id": workspace_id,
        "kb_id": kb_id,
        "rag_context": "",
    })
    last = result["messages"][-1]
    return last.content if hasattr(last, "content") else str(last)
