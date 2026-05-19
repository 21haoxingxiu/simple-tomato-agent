"""Mistral chat model provider."""
from __future__ import annotations

from typing import Any, Optional

from models.base import BaseChatModel
from models.factory import register_chat_provider


@register_chat_provider("mistral")
class MistralChatModel(BaseChatModel):
    """Mistral chat model wrapper using OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        model: str = "mistral-large-latest",
        temperature: float = 0.3,
        **kwargs: Any,
    ):
        from langchain_openai import ChatOpenAI
        self._model = model
        self._chat = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://api.mistral.ai/v1",
            temperature=temperature,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, messages: list[dict], **kwargs: Any) -> Any:
        lc_messages = self._convert_messages(messages)
        return self._chat.invoke(lc_messages, **kwargs)

    def stream(self, messages: list[dict], **kwargs: Any):
        lc_messages = self._convert_messages(messages)
        for chunk in self._chat.stream(lc_messages, **kwargs):
            yield chunk

    def _convert_messages(self, messages: list[dict]) -> list:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        result = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
        return result
