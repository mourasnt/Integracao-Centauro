# app/api/deps.py
"""
Centralized FastAPI dependencies.
All route dependencies should be imported from here.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.config.settings import settings
from app.services.vblog.base import VBlogBaseClient
from app.services.vblog.transito import VBlogTransitoService
from app.services.vblog.tracking import VBlogTrackingService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async database session.
    Use as: db: AsyncSession = Depends(get_db)
    """
    async for session in _get_db():
        yield session


def get_vblog_service() -> VBlogTransitoService:
    """
    Provides VBlogTransitoService configured from settings.
    Use as: vblog: VBlogTransitoService = Depends(get_vblog_service)
    """
    return VBlogTransitoService(
        cnpj=settings.vblog_cnpj,
        token=settings.vblog_token,
        base_url=settings.vblog_base,
    )


def get_tracking_service() -> VBlogTrackingService:
    """
    Provides VBlogTrackingService configured from settings.
    Use as: tracking: VBlogTrackingService = Depends(get_tracking_service)
    """
    return VBlogTrackingService(
        usuario=settings.brudam_usuario,
        senha=settings.brudam_senha,
        endpoint=settings.brudam_url_tracking,
        cliente=settings.brudam_cliente,
    )
