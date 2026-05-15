from pydantic import BaseModel, Field
from typing import Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    workspace_id: str = "default"
    knowledge_base_id: str | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    message: ChatMessage
    usage: dict = Field(default_factory=dict)
