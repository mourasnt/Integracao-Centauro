# app/services/shipment_service.py
"""
Shipment service (formerly carga_service.py).
CRUD operations for shipments using async SQLAlchemy.
"""

from uuid import UUID
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.shipment import Shipment
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.utils.logger import logger


class ShipmentService:
    """Service for shipment CRUD operations."""

    @staticmethod
    async def create(db: AsyncSession, data: ShipmentCreate) -> Shipment:
        """Create a new shipment."""
        shipment = Shipment(**data.model_dump())
        db.add(shipment)
        await db.commit()
        await db.refresh(shipment)
        logger.info(f"Created shipment: {shipment.id}")
        return shipment

    @staticmethod
    async def list_all(db: AsyncSession) -> List[Shipment]:
        """List all shipments with relationships."""
        result = await db.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.client_ctes),
                selectinload(Shipment.subcontracted_ctes),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, shipment_id: UUID) -> Optional[Shipment]:
        """Get shipment by ID with relationships."""
        result = await db.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.client_ctes),
                selectinload(Shipment.subcontracted_ctes),
            )
            .where(Shipment.id == shipment_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_external_id(db: AsyncSession, external_id: str) -> Optional[Shipment]:
        """Get shipment by external ID."""
        result = await db.execute(
            select(Shipment)
            .options(
                selectinload(Shipment.client_ctes),
                selectinload(Shipment.subcontracted_ctes),
            )
            .where(Shipment.external_id == external_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        shipment_id: UUID,
        data: ShipmentUpdate,
    ) -> Optional[Shipment]:
        """Update a shipment."""
        shipment = await ShipmentService.get_by_id(db, shipment_id)
        if not shipment:
            return None

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(shipment, field, value)

        await db.commit()
        await db.refresh(shipment)
        logger.info(f"Updated shipment: {shipment.id}")
        return shipment

    @staticmethod
    async def delete(db: AsyncSession, shipment_id: UUID) -> bool:
        """Delete a shipment."""
        shipment = await ShipmentService.get_by_id(db, shipment_id)
        if not shipment:
            return False
        
        await db.delete(shipment)
        await db.commit()
        logger.info(f"Deleted shipment: {shipment_id}")
        return True
