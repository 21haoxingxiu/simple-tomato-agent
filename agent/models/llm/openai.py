"""OpenAI chat model provider."""
from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Optional

from langchain_openai import ChatOpenAI

from models.base import BaseChatModel
from models.factory import register_chat_provider


@register_chat_provider("openai")
class OpenAIChatModel(BaseChatModel):
    """OpenAI chat model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs: Any,
    ):
        self._model = model
        self._chat = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, messages: list[dict], **kwargs: Any) -> Any:
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        lc_messages = self._convert_messages(messages)
        return self._chat.invoke(lc_messages, **kwargs)

    def stream(self, messages: list[dict], **kwargs: Any) -> Iterator[Any]:
        lc_messages = self._convert_messages(messages)
        for chunk in self._chat.stream(lc_messages, **kwargs):
            yield chunk

    async def ainvoke(self, messages: list[dict], **kwargs: Any) -> Any:
        lc_messages = self._convert_messages(messages)
        return await self._chat.ainvoke(lc_messages, **kwargs)

    async def astream(self, messages: list[dict], **kwargs: Any) -> AsyncIterator[Any]:
        lc_messages = self._convert_messages(messages)
        async for chunk in self._chat.astream(lc_messages, **kwargs):
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
