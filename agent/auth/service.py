"""用户认证服务:bcrypt 密码哈希 + JWT 签发/校验。

JWT_SECRET 必须与 Go Gateway 中间件保持一致(同 env 注入)。
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "dev-secret-change-in-prod")


def _jwt_alg() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _token_ttl_hours() -> int:
    try:
        return int(os.getenv("JWT_TTL_HOURS", "24"))
    except ValueError:
        return 24


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return _pwd.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(
    *,
    user_id: str,
    email: str,
    workspace_id: str,
    extra: Optional[dict] = None,
    ttl_hours: Optional[int] = None,
) -> str:
    """签发 JWT。声明字段需与 Go Gateway middleware/auth.go 一致:user_id / workspace_id。"""
    now = datetime.now(timezone.utc)
    payload: dict = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "sub": email,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(hours=ttl_hours or _token_ttl_hours())).timestamp()
        ),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _jwt_secret(), algorithm=_jwt_alg())


def decode_token(token: str) -> dict:
    return jwt.decode(token, _jwt_secret(), algorithms=[_jwt_alg()])
