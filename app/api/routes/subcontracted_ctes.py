# app/api/routes/subcontracted_ctes.py
"""
Subcontracted CTe API routes (formerly subcontratacao.py).
Handles XML upload and VBLOG integration for subcontracted CTes.
"""

from uuid import UUID
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_vblog_service
from app.services.shipment_service import ShipmentService
from app.services.crypto_service import encrypt_text
from app.services.vblog.transito import VBlogTransitoService
from app.services.vblog.envdocs import VBlogEnvDocsService
from app.models.subcontracted_cte import SubcontractedCTe
from app.schemas.subcontracted_cte import SubcontractedCTeRead, SubcontractedCTeWithVBlog
from app.utils.logger import logger


router = APIRouter()


def extract_key_from_xml(xml_str: str) -> str | None:
    """Extract CTe access key from XML content."""
    try:
        root = ET.fromstring(xml_str)
        ns = {"cte": "http://www.portalfiscal.inf.br/cte"}
        
        key_elem = root.find(".//cte:chCTe", ns)
        if key_elem is not None and key_elem.text:
            return key_elem.text.strip()
    except Exception as e:
        logger.error(f"Error extracting key from XML: {e}")
    return None


@router.post("/upload-xml", response_model=dict)
async def upload_subcontracted_xml(
    shipment_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
):
    """
    Upload subcontracted CTe XML and send to VBLOG.
    
    The XML is stored encrypted and sent to VBLOG for processing.
    """
    # Verify shipment exists
    shipment = await ShipmentService.get_by_id(db, shipment_id)
    if not shipment:
        raise HTTPException(404, "Shipment not found")

    # Read and parse XML
    content = await file.read()
    xml_str = content.decode("utf-8")

    # Extract access key
    access_key = extract_key_from_xml(xml_str)
    if not access_key:
        raise HTTPException(400, "Could not extract CTe key from XML")

    # Check for duplicates
    result = await db.execute(
        select(SubcontractedCTe).where(SubcontractedCTe.access_key == access_key)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"CTe already exists: {access_key}")

    # Create subcontracted CTe record
    subcontracted = SubcontractedCTe(
        shipment_id=shipment_id,
        access_key=access_key,
    )
    subcontracted.xml = xml_str  # Encrypted on assignment
    db.add(subcontracted)

    # Send to VBLOG
    envdocs_service = VBlogEnvDocsService(vblog)
    try:
        vblog_result = await envdocs_service.upload_ctes([xml_str])
        
        subcontracted.vblog_status_code = str(vblog_result.get("code", ""))
        subcontracted.vblog_status_description = vblog_result.get("description", "")
        subcontracted.vblog_raw_response = str(vblog_result)[:2000]
        subcontracted.vblog_attempts = 1
        
        logger.info(f"Subcontracted CTe uploaded: {access_key}")
        
    except Exception as e:
        logger.error(f"VBLOG upload failed for {access_key}: {e}")
        subcontracted.vblog_status_code = "ERROR"
        subcontracted.vblog_status_description = str(e)[:500]
        subcontracted.vblog_attempts = 1

    await db.commit()
    await db.refresh(subcontracted)

    return {
        "id": str(subcontracted.id),
        "access_key": access_key,
        "vblog_status": subcontracted.vblog_status_code,
        "message": "CTe uploaded and sent to VBLOG",
    }


@router.get("/{cte_id}", response_model=SubcontractedCTeRead)
async def get_subcontracted_cte(
    cte_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get subcontracted CTe by ID."""
    result = await db.execute(
        select(SubcontractedCTe).where(SubcontractedCTe.id == cte_id)
    )
    cte = result.scalar_one_or_none()
    if not cte:
        raise HTTPException(404, "Subcontracted CTe not found")
    return cte


@router.post("/{cte_id}/retry-vblog", response_model=dict)
async def retry_vblog_upload(
    cte_id: UUID,
    db: AsyncSession = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
):
    """Retry sending subcontracted CTe to VBLOG."""
    result = await db.execute(
        select(SubcontractedCTe).where(SubcontractedCTe.id == cte_id)
    )
    cte = result.scalar_one_or_none()
    if not cte:
        raise HTTPException(404, "Subcontracted CTe not found")

    if not cte.xml:
        raise HTTPException(400, "CTe has no stored XML")

    envdocs_service = VBlogEnvDocsService(vblog)
    try:
        vblog_result = await envdocs_service.upload_ctes([cte.xml])
        
        cte.vblog_status_code = str(vblog_result.get("code", ""))
        cte.vblog_status_description = vblog_result.get("description", "")
        cte.vblog_raw_response = str(vblog_result)[:2000]
        cte.vblog_attempts += 1
        
        await db.commit()
        
        return {
            "status": "ok",
            "vblog_code": cte.vblog_status_code,
            "attempts": cte.vblog_attempts,
        }
        
    except Exception as e:
        cte.vblog_status_code = "ERROR"
        cte.vblog_status_description = str(e)[:500]
        cte.vblog_attempts += 1
        await db.commit()
        
        raise HTTPException(500, f"VBLOG upload failed: {e}")
