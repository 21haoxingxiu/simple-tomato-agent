from fastapi import APIRouter, Header
from pydantic import BaseModel

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeBase(BaseModel):
    id: str
    name: str
    doc_count: int
    status: str


MOCK_BASES = [
    KnowledgeBase(id="kb-1", name="产品文档", doc_count=24, status="ready"),
    KnowledgeBase(id="kb-2", name="技术规范", doc_count=8, status="indexing"),
]


@router.get("/bases")
async def list_bases(x_workspace_id: str = Header(default="default")):
    return {"workspace_id": x_workspace_id, "items": MOCK_BASES}


@router.post("/bases")
async def create_base(body: KnowledgeBase, x_workspace_id: str = Header(default="default")):
    return {"workspace_id": x_workspace_id, "created": body}
