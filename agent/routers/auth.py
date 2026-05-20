from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from db.database import get_session
from db.models import User, Workspace

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------- schemas ----------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str] = None
    default_workspace_id: str
    created_at: str


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    avatar_url: Optional[str] = Field(None, max_length=500)


class AuthResponse(BaseModel):
    token: str
    user: UserOut


# ---------------- helpers ----------------


def _user_to_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        email=u.email,
        name=u.name or "",
        avatar_url=u.avatar_url,
        default_workspace_id=u.default_workspace_id,
        created_at=u.created_at.isoformat(),
    )


def _derive_name(email: str, override: Optional[str]) -> str:
    if override and override.strip():
        return override.strip()[:120]
    local = email.split("@", 1)[0]
    return re.sub(r"[^\w\-\s]", "", local)[:120] or "新用户"


# ---------------- routes ----------------


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_session)):
    email = body.email.lower().strip()
    existed = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existed:
        raise HTTPException(status_code=409, detail="该邮箱已被注册")

    name = _derive_name(email, body.name)
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(body.password),
        default_workspace_id="pending",
    )
    session.add(user)
    await session.flush()

    workspace = Workspace(name="默认工作区", description="自动创建", owner_id=user.id)
    session.add(workspace)
    await session.flush()

    user.default_workspace_id = workspace.id
    user.last_login_at = datetime.utcnow()
    await session.commit()
    await session.refresh(user)

    token = create_access_token(
        user_id=user.id, email=user.email, workspace_id=workspace.id
    )
    return AuthResponse(token=token, user=_user_to_out(user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    email = body.email.lower().strip()
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")

    user.last_login_at = datetime.utcnow()
    await session.commit()

    token = create_access_token(
        user_id=user.id, email=user.email, workspace_id=user.default_workspace_id
    )
    return AuthResponse(token=token, user=_user_to_out(user))


@router.get("/me", response_model=UserOut)
async def me(
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    user = await session.get(User, payload.get("user_id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return _user_to_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdateRequest,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    """更新当前用户信息（名称和头像）"""
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    user = await session.get(User, payload.get("user_id", ""))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新用户信息
    if body.name is not None:
        user.name = body.name.strip()[:120]
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url

    await session.commit()
    await session.refresh(user)
    return _user_to_out(user)


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None


class WorkspaceOut(BaseModel):
    id: str
    name: str
    description: str
    owner_id: str
    created_at: str


@router.get("/workspaces")
async def list_workspaces(
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    res = await session.execute(
        select(Workspace).where(Workspace.owner_id == payload.get("user_id", ""))
    )
    items = res.scalars().all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "created_at": w.created_at.isoformat(),
        }
        for w in items
    ]


@router.post("/workspaces", response_model=WorkspaceOut)
async def create_workspace(
    body: WorkspaceCreate,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    user_id = payload.get("user_id", "")
    workspace = Workspace(
        name=body.name,
        description=body.description or "",
        owner_id=user_id,
    )
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at.isoformat(),
    )


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(
    workspace_id: str,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    workspace = await session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != payload.get("user_id", ""):
        raise HTTPException(status_code=404, detail="工作区不存在")
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at.isoformat(),
    )


@router.patch("/workspaces/{workspace_id}", response_model=WorkspaceOut)
async def update_workspace(
    workspace_id: str,
    body: WorkspaceUpdate,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    workspace = await session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != payload.get("user_id", ""):
        raise HTTPException(status_code=404, detail="工作区不存在")
    if body.name is not None:
        workspace.name = body.name
    if body.description is not None:
        workspace.description = body.description
    await session.commit()
    await session.refresh(workspace)
    return WorkspaceOut(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        owner_id=workspace.owner_id,
        created_at=workspace.created_at.isoformat(),
    )


@router.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
):
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="未提供 token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"token 无效: {exc}") from exc

    workspace = await session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != payload.get("user_id", ""):
        raise HTTPException(status_code=404, detail="工作区不存在")

    # Prevent deleting the last workspace
    count = await session.execute(
        select(Workspace).where(Workspace.owner_id == payload.get("user_id", ""))
    )
    if len(count.scalars().all()) <= 1:
        raise HTTPException(status_code=400, detail="无法删除最后一个工作区")

    await session.delete(workspace)
    await session.commit()
    return {"ok": True, "deleted_id": workspace_id}
