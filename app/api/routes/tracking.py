# app/api/routes/tracking.py
"""
Tracking API routes.
Handles tracking event operations and resending.
"""

from uuid import UUID
import datetime

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_tracking_service
from app.services.client_cte_service import ClientCTeService
from app.services.tracking_event_service import TrackingEventService
from app.services.vblog.tracking import VBlogTrackingService
from app.services.constants import VALID_CODES
from app.schemas.tracking_event import TrackingEventCreate, TrackingEventRead
from app.utils.logger import logger


router = APIRouter()


@router.post("/tracking/{cte_id}/resend")
async def resend_tracking(
    cte_id: UUID,
    event_code: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    tracking_service: VBlogTrackingService = Depends(get_tracking_service),
):
    """
    Resend a tracking event for a specific CTe.
    
    Useful for retrying failed tracking submissions.
    """
    if event_code not in VALID_CODES:
        raise HTTPException(400, "Invalid VBLOG event code")

    cte = await ClientCTeService.get_by_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CTe not found")

    # Send tracking event
    success, response_text = await tracking_service.send(
        document_key=cte.access_key,
        event_code=event_code,
    )

    # Register tracking event
    await TrackingEventService.register(
        db,
        TrackingEventCreate(
            client_cte_id=cte.id,
            event_code=event_code,
            description=VALID_CODES[event_code]["message"],
            event_date=datetime.datetime.now(datetime.timezone.utc),
        ),
    )

    logger.info(f"Tracking resent for CTe {cte.access_key}: code {event_code}")

    return {
        "ok": success,
        "vblog_response": response_text,
    }


@router.get("/tracking/{cte_id}/events", response_model=list[TrackingEventRead])
async def list_tracking_events(
    cte_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all tracking events for a CTe."""
    cte = await ClientCTeService.get_by_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CTe not found")

    return await TrackingEventService.list_by_cte(db, cte_id)
