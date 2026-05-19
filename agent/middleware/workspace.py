"""Workspace validation dependency for FastAPI."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import Workspace


async def get_valid_workspace_id(
    x_workspace_id: str = Header(default="default", alias="X-Workspace-ID"),
    x_user_id: str = Header(default="anonymous", alias="X-User-ID"),
    session: AsyncSession = Depends(get_session),
) -> str:
    """
    Validate that the workspace exists and belongs to the user.
    Returns the workspace ID if valid.

    For anonymous users (x_user_id="anonymous"), always allows "default" workspace.
    """
    # For anonymous users, allow "default" workspace without validation
    if x_user_id == "anonymous":
        return x_workspace_id

    # Validate workspace ownership
    workspace = await session.get(Workspace, x_workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="工作区不存在")
    if workspace.owner_id != x_user_id:
        raise HTTPException(status_code=403, detail="无权访问此工作区")

    return x_workspace_id
