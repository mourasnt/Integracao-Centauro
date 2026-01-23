# app/core/database.py
"""
Async SQLAlchemy database configuration with thread-safe initialization.
"""

import asyncio
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config.settings import settings


# Create async engine with appropriate settings
engine_kwargs = {
    "echo": False,
}

# SQLite-specific settings for async
if "sqlite" in settings.database_url:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = StaticPool

async_engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Thread-safe initialization lock
_db_init_lock = asyncio.Lock()
_db_initialized = False


async def ensure_db_initialized() -> None:
    """
    Ensure database tables are created. Thread-safe and idempotent.
    Uses double-checked locking pattern.
    """
    global _db_initialized
    if _db_initialized:
        return
    
    async with _db_init_lock:
        if _db_initialized:
            return
        
        from app.models.base import Base
        
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        _db_initialized = True


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    Ensures database is initialized before yielding session.
    """
    await ensure_db_initialized()
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Legacy sync engine for backward compatibility during migration
# TODO: Remove after full async migration
sync_database_url = settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "+psycopg2")
engine = create_engine(sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
