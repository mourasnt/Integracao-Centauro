# app/services/tracking_event_service.py
"""
TrackingEvent service (formerly tracking_service.py).
CRUD operations for tracking events using async SQLAlchemy.
"""

from uuid import UUID
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tracking_event import TrackingEvent
from app.schemas.tracking_event import TrackingEventCreate
from app.utils.logger import logger


class TrackingEventService:
    """Service for tracking event CRUD operations."""

    @staticmethod
    async def register(db: AsyncSession, data: TrackingEventCreate) -> TrackingEvent:
        """Register a new tracking event."""
        tracking = TrackingEvent(**data.model_dump())
        db.add(tracking)
        await db.commit()
        await db.refresh(tracking)
        logger.info(
            f"Registered tracking event: {tracking.event_code} for CTe {tracking.client_cte_id}"
        )
        return tracking

    @staticmethod
    async def list_by_cte(db: AsyncSession, cte_id: UUID) -> List[TrackingEvent]:
        """List all tracking events for a CTe."""
        result = await db.execute(
            select(TrackingEvent)
            .where(TrackingEvent.client_cte_id == cte_id)
            .order_by(TrackingEvent.event_date)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_latest_by_cte(db: AsyncSession, cte_id: UUID) -> TrackingEvent | None:
        """Get the most recent tracking event for a CTe."""
        result = await db.execute(
            select(TrackingEvent)
            .where(TrackingEvent.client_cte_id == cte_id)
            .order_by(TrackingEvent.event_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
