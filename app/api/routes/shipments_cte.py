# app/api/routes/shipments_cte.py
"""
CTe operations for shipments.
"""

from uuid import UUID
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.client_cte_service import ClientCTeService
from app.schemas.client_cte import ClientCTeRead


router = APIRouter()


@router.get("/cte/{cte_id}", response_model=ClientCTeRead)
async def get_cte(
    cte_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a client CTe by ID."""
    cte = await ClientCTeService.get_by_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CTe not found")
    return cte


@router.get("/cte/{cte_id}/download")
async def download_cte_xml(
    cte_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Download CTe XML file."""
    cte = await ClientCTeService.get_by_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CTe not found")
    
    if not cte.xml:
        raise HTTPException(400, "CTe has no stored XML")
    
    xml_bytes = cte.xml.encode("utf-8")
    file_stream = BytesIO(xml_bytes)
    filename = f"cte-{cte.id}.xml"
    
    return StreamingResponse(
        file_stream,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
