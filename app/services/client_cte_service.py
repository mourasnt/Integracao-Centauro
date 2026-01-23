# app/services/client_cte_service.py
"""
ClientCTe service (formerly cte_cliente_service.py).
CRUD operations for client CTe documents using async SQLAlchemy.
"""

from uuid import UUID
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.client_cte import ClientCTe
from app.schemas.client_cte import ClientCTeCreate
from app.utils.logger import logger


class ClientCTeService:
    """Service for client CTe CRUD operations."""

    @staticmethod
    async def add(
        db: AsyncSession,
        shipment_id: UUID,
        data: ClientCTeCreate,
    ) -> ClientCTe:
        """Add a new client CTe to a shipment."""
        cte = ClientCTe(
            shipment_id=shipment_id,
            access_key=data.access_key,
        )
        cte.xml = data.xml  # Triggers encryption
        db.add(cte)
        await db.commit()
        await db.refresh(cte)
        logger.info(f"Added client CTe: {cte.access_key}")
        return cte

    @staticmethod
    async def list_by_shipment(db: AsyncSession, shipment_id: UUID) -> List[ClientCTe]:
        """List all client CTes for a shipment."""
        result = await db.execute(
            select(ClientCTe)
            .options(selectinload(ClientCTe.tracking_events))
            .where(ClientCTe.shipment_id == shipment_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, cte_id: UUID) -> Optional[ClientCTe]:
        """Get client CTe by ID."""
        result = await db.execute(
            select(ClientCTe)
            .options(selectinload(ClientCTe.tracking_events))
            .where(ClientCTe.id == cte_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_access_key(
        db: AsyncSession, 
        access_key: str,
    ) -> Optional[ClientCTe]:
        """Get client CTe by access key."""
        result = await db.execute(
            select(ClientCTe)
            .options(selectinload(ClientCTe.tracking_events))
            .where(ClientCTe.access_key == access_key)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_xml(
        db: AsyncSession,
        cte: ClientCTe,
        xml: str,
    ) -> ClientCTe:
        """Update CTe XML (encrypted)."""
        cte.xml = xml
        await db.commit()
        await db.refresh(cte)
        logger.info(f"Updated XML for CTe: {cte.access_key}")
        return cte

    @staticmethod
    async def update_invoices(
        db: AsyncSession,
        cte: ClientCTe,
        invoices: List[str],
    ) -> ClientCTe:
        """Update associated NF-e invoices."""
        cte.invoices = invoices
        await db.commit()
        await db.refresh(cte)
        logger.info(f"Updated invoices for CTe: {cte.access_key}")
        return cte
