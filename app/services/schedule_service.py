# app/services/schedule_service.py
"""
Schedule service (formerly agendamento_service.py).
CRUD operations for schedules using async SQLAlchemy.
"""

from uuid import UUID
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.schedule import Schedule
from app.schemas.schedule import ScheduleCreate
from app.utils.logger import logger


class ScheduleService:
    """Service for schedule CRUD operations."""

    @staticmethod
    async def create_or_update(db: AsyncSession, data: ScheduleCreate) -> Schedule:
        """Create or update a schedule for a shipment."""
        result = await db.execute(
            select(Schedule).where(Schedule.shipment_id == data.shipment_id)
        )
        schedule = result.scalar_one_or_none()

        if schedule:
            # Update existing
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(schedule, field, value)
            logger.info(f"Updated schedule for shipment: {data.shipment_id}")
        else:
            # Create new
            schedule = Schedule(**data.model_dump())
            db.add(schedule)
            logger.info(f"Created schedule for shipment: {data.shipment_id}")

        await db.commit()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def get_by_shipment(db: AsyncSession, shipment_id: UUID) -> Optional[Schedule]:
        """Get schedule by shipment ID."""
        result = await db.execute(
            select(Schedule).where(Schedule.shipment_id == shipment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, schedule_id: UUID) -> Optional[Schedule]:
        """Get schedule by ID."""
        result = await db.execute(
            select(Schedule).where(Schedule.id == schedule_id)
        )
        return result.scalar_one_or_none()
