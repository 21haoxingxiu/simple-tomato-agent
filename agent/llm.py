"""LLM 工厂:统一封装 OpenAI / 智谱(GLM) / 任意 OpenAI 兼容服务。

- OPENAI_API_KEY:Key 字符串
- OPENAI_BASE_URL:可选,自定义 base url(智谱 / Ollama / OneAPI / vLLM 都 OK)
- OPENAI_MODEL:对话模型
- OPENAI_JUDGE_MODEL:评测裁判模型(可省略,默认与 OPENAI_MODEL 相同)
"""
from __future__ import annotations

import os
from typing import Optional

from langchain_openai import ChatOpenAI


def _has_valid_key() -> bool:
    k = os.getenv("OPENAI_API_KEY", "").strip()
    if not k:
        return False
    if k.startswith("sk-placeholder") or k == "sk-your-key-here":
        return False
    return len(k) >= 16


def is_llm_configured() -> bool:
    return _has_valid_key()


def _base_url() -> Optional[str]:
    url = os.getenv("OPENAI_BASE_URL", "").strip()
    return url or None


def get_chat_model(
    *,
    model: Optional[str] = None,
    temperature: float = 0.3,
    streaming: bool = False,
) -> ChatOpenAI:
    """返回配置好的 ChatOpenAI 实例(兼容智谱 / 任意 OpenAI 协议端点)。"""
    return ChatOpenAI(
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-placeholder"),
        base_url=_base_url(),
        temperature=temperature,
        streaming=streaming,
    )


def get_judge_model(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_JUDGE_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY", "sk-placeholder"),
        base_url=_base_url(),
        temperature=temperature,
    )
