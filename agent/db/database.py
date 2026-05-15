"""
Database setup — SQLite for development, PostgreSQL for production.
Switch via DATABASE_URL environment variable.
"""
from __future__ import annotations

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/agentstudio.db"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("ENV") == "development",
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
