"""
LangGraph-based chat agent.

Graph structure:
  START → router → [retriever | direct_llm] → generator → END
"""

import os
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    workspace_id: str
    use_retrieval: bool


def _build_graph() -> StateGraph:
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-placeholder"),
        temperature=0.7,
    )

    def router(state: AgentState) -> dict:
        """Decide whether to use RAG or direct LLM."""
        last = state["messages"][-1]
        # Simple heuristic: use retrieval when knowledge_base is specified
        return {"use_retrieval": state.get("use_retrieval", False)}

    def retriever(state: AgentState) -> dict:
        """Placeholder: fetch relevant chunks from vector store."""
        context = "[RAG] 向量检索功能待实现，将从知识库中检索相关内容。"
        system_msg = SystemMessage(content=f"参考以下背景知识回答问题：\n{context}")
        return {"messages": [system_msg]}

    def generator(state: AgentState) -> dict:
        """Call LLM to generate response."""
        try:
            response = llm.invoke(state["messages"])
            return {"messages": [response]}
        except Exception as exc:
            fallback = AIMessage(content=f"[Demo 模式] LLM 未配置，这是占位响应。错误: {exc}")
            return {"messages": [fallback]}

    def route_condition(state: AgentState) -> str:
        return "retriever" if state.get("use_retrieval") else "generator"

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


# Compiled graph (singleton)
chat_graph = _build_graph()


async def run_chat(messages: list[dict], workspace_id: str = "default", use_retrieval: bool = False) -> str:
    """Run the chat agent and return the assistant's reply."""
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
        "use_retrieval": use_retrieval,
    })

    last_msg = result["messages"][-1]
    return last_msg.content if hasattr(last_msg, "content") else str(last_msg)
