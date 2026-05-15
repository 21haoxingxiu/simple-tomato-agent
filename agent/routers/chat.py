from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from schemas.chat import ChatRequest, ChatResponse, ChatMessage
from agents.chat_agent import run_chat

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    x_user_id: str = Header(default="anonymous"),
    x_workspace_id: str = Header(default="default"),
):
    workspace = x_workspace_id or request.workspace_id
    messages = [m.model_dump() for m in request.messages]

    content = await run_chat(
        messages=messages,
        workspace_id=workspace,
        use_retrieval=request.knowledge_base_id is not None,
    )

    return ChatResponse(
        message=ChatMessage(role="assistant", content=content),
        usage={"workspace_id": workspace},
    )
