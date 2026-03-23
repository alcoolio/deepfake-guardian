"""Async SQLAlchemy database setup.

Default backend: SQLite via aiosqlite (zero-config, single-file).
For production set DATABASE_URL to a PostgreSQL asyncpg URL:
    postgresql+asyncpg://user:password@host/dbname
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

engine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables if they do not exist (idempotent)."""
    import db_models  # noqa: F401 — side-effect: registers ORM models with Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency — yields a scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
