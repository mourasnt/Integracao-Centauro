# app/api/routes/shipments_crud.py
"""
Shipment CRUD operations.
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.shipment_service import ShipmentService
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentRead


router = APIRouter()


@router.get("/", response_model=List[ShipmentRead])
async def list_shipments(db: AsyncSession = Depends(get_db)):
    """List all shipments."""
    return await ShipmentService.list_all(db)


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def get_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a shipment by ID."""
    shipment = await ShipmentService.get_by_id(db, shipment_id)
    if not shipment:
        raise HTTPException(404, "Shipment not found")
    return shipment


@router.post("/", response_model=ShipmentRead, status_code=201)
async def create_shipment(
    data: ShipmentCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new shipment."""
    return await ShipmentService.create(db, data)


@router.put("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: UUID,
    data: ShipmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a shipment."""
    shipment = await ShipmentService.update(db, shipment_id, data)
    if not shipment:
        raise HTTPException(404, "Shipment not found")
    return shipment


@router.delete("/{shipment_id}")
async def delete_shipment(
    shipment_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a shipment."""
    deleted = await ShipmentService.delete(db, shipment_id)
    if not deleted:
        raise HTTPException(404, "Shipment not found")
    return {"status": "deleted"}
