# app/api/routes/schedules.py
"""
Schedule API routes (formerly agendamentos.py).
Handles schedule (ETA/ETD) operations for shipments.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.shipment_service import ShipmentService
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import ScheduleCreate, ScheduleRead


router = APIRouter()


@router.get("/{shipment_id}/schedule", response_model=ScheduleRead)
async def get_schedule(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get schedule for a shipment."""
    schedule = await ScheduleService.get_by_shipment(db, shipment_id)
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    return schedule


@router.put("/{shipment_id}/schedule", response_model=ScheduleRead)
async def update_schedule(
    shipment_id: UUID,
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update schedule for a shipment."""
    # Validate shipment_id matches route
    if data.shipment_id != shipment_id:
        raise HTTPException(
            400,
            "shipment_id in body must match route parameter",
        )

    # Verify shipment exists
    shipment = await ShipmentService.get_by_id(db, shipment_id)
    if not shipment:
        raise HTTPException(404, "Shipment not found")

    return await ScheduleService.create_or_update(db, data)
