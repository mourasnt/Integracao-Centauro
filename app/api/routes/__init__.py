# app/api/routes/__init__.py
"""
API routes package.
Contains all endpoint definitions organized by resource.
"""

from fastapi import APIRouter

from . import shipments
from . import subcontracted_ctes
from . import tracking
from . import locations

# Main router that includes all sub-routers
api_router = APIRouter()

api_router.include_router(
    shipments.router,
    prefix="/shipments",
    tags=["Shipments"],
)


api_router.include_router(
    subcontracted_ctes.router,
    prefix="/subcontracted-ctes",
    tags=["Subcontracted CTes"],
)

api_router.include_router(
    tracking.router,
    tags=["Tracking"],
)

api_router.include_router(
    locations.router,
    prefix="/locations",
    tags=["Locations"],
)
