"""
Database setup — SQLite for development, PostgreSQL for production.
Switch via DATABASE_URL environment variable.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite+aiosqlite:///./data/agentstudio.db"
)

if DATABASE_URL.startswith("sqlite"):
    # 自动建立 data 目录
    db_path = DATABASE_URL.split("///")[-1]
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "").lower() == "true",
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
