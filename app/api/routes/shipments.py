# app/api/routes/shipments.py
"""
Shipment API routes - Aggregates all shipment-related routes.

This module combines routes from:
- shipments_crud: Basic CRUD operations
- shipments_cte: CTe document operations
- shipments_status: Status update with tracking
- shipments_sync: VBLOG synchronization
"""

from fastapi import APIRouter

from .shipments_crud import router as crud_router
from .shipments_cte import router as cte_router
from .shipments_status import router as status_router
from .shipments_sync import router as sync_router


router = APIRouter()

# Include all sub-routers
router.include_router(crud_router)
router.include_router(cte_router)
router.include_router(status_router)
router.include_router(sync_router)