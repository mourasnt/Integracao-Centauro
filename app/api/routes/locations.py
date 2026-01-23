# app/api/routes/locations.py
"""
Location API routes (formerly localidades.py).
Handles state and municipality operations including IBGE sync.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.location_service import LocationService
from app.schemas.location import StateRead, MunicipalityRead


router = APIRouter()


@router.get("/states", response_model=list[StateRead])
async def list_states(db: AsyncSession = Depends(get_db)):
    """List all Brazilian states."""
    return await LocationService.get_states(db)


@router.get("/states/{abbreviation}/municipalities", response_model=list[MunicipalityRead])
async def list_municipalities_by_state(
    abbreviation: str,
    db: AsyncSession = Depends(get_db),
):
    """List all municipalities in a state."""
    municipalities = await LocationService.get_municipalities_by_state(db, abbreviation)
    if municipalities is None:
        raise HTTPException(404, "State not found")
    return municipalities


@router.get("/municipalities/{ibge_code}", response_model=MunicipalityRead)
async def get_municipality(
    ibge_code: int,
    db: AsyncSession = Depends(get_db),
):
    """Get municipality by IBGE code."""
    municipality = await LocationService.get_municipality_by_code(db, ibge_code)
    if not municipality:
        raise HTTPException(404, "Municipality not found")
    return municipality


@router.post("/sync")
async def sync_locations(db: AsyncSession = Depends(get_db)):
    """
    Synchronize states and municipalities from IBGE API.
    
    This operation may take a few seconds as it fetches and updates
    all Brazilian states and municipalities.
    """
    stats = await LocationService.sync_with_ibge(db)
    return {
        "status": "ok",
        "message": "Locations synchronized with IBGE",
        "stats": stats,
    }
