"""ZhipuAI chat model provider."""
from __future__ import annotations

from typing import Any, Optional

from models.base import BaseChatModel
from models.factory import register_chat_provider


@register_chat_provider("zhipuai")
class ZhipuAIChatModel(BaseChatModel):
    """ZhipuAI chat model wrapper."""

    def __init__(
        self,
        api_key: str,
        model: str = "glm-4-flash",
        temperature: float = 0.3,
        **kwargs: Any,
    ):
        self._model = model
        self._api_key = api_key
        self._temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from zhipuai import ZhipuAI
                self._client = ZhipuAI(api_key=self._api_key)
            except ImportError:
                raise ImportError("zhipuai package required: pip install zhipuai")
        return self._client

    @property
    def model_name(self) -> str:
        return self._model

    def invoke(self, messages: list[dict], **kwargs: Any) -> Any:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
        )
        return response

    def stream(self, messages: list[dict], **kwargs: Any):
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=self._temperature,
            stream=True,
        )
        for chunk in response:
            yield chunk
