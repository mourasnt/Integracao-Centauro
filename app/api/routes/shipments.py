# app/api/routes/shipments.py
"""
Shipment API routes (formerly cargas.py).
Handles CRUD operations and VBLOG integration for shipments.
"""

from uuid import UUID
from typing import Optional, Any, List
from io import BytesIO
import json
import base64
import datetime
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException, Body, Request, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.api.deps import get_db, get_vblog_service, get_tracking_service
from app.services.shipment_service import ShipmentService
from app.services.client_cte_service import ClientCTeService
from app.services.tracking_event_service import TrackingEventService
from app.services.attachments_service import AttachmentService
from app.services.vblog.transito import VBlogTransitoService
from app.services.vblog.tracking import VBlogTrackingService
from app.services.vblog.cte import VBlogCTeService
from app.services.constants import VALID_CODES, VALID_CODES_SET
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentRead
from app.schemas.client_cte import ClientCTeRead, ClientCTeCreate
from app.schemas.tracking_event import TrackingEventCreate
from app.models.shipment import ShipmentStatus
from app.utils.logger import logger


router = APIRouter()


# ---------------------------
# CRUD Operations
# ---------------------------

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


# ---------------------------
# CTe Operations
# ---------------------------

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


# ---------------------------
# Status Update with Tracking
# ---------------------------

@router.post("/{shipment_id}/status")
async def update_status(
    shipment_id: UUID,
    new_status: Optional[Any] = Body(None, example={"code": "1"}),
    attachment: Optional[UploadFile] = File(None),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    tracking_service: VBlogTrackingService = Depends(get_tracking_service),
):
    """
    Update shipment status and send tracking events to Brudam.
    
    Accepts status code in various formats:
    - Raw code: "1" or 1
    - JSON string: '{"code": "1"}'
    - Object: {"code": "1"}
    """
    shipment = await ShipmentService.get_by_id(db, shipment_id)
    if not shipment:
        raise HTTPException(404, "Shipment not found")

    # Parse multipart form if applicable
    if request and request.headers.get("content-type", "").startswith("multipart/"):
        try:
            form = await request.form()
            status_json = form.get("novo_status_json") or form.get("novo_status") or form.get("new_status")
            if status_json:
                try:
                    from app.schemas.shipment import ShipmentStatusInput
                    new_status = ShipmentStatusInput.model_validate_json(status_json)
                except Exception as e:
                    raise HTTPException(400, f"Error parsing status from form: {e}")
        except Exception:
            pass

    # Parse attachments from JSON body
    attachments_input = None
    try:
        if request and request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
            if isinstance(body, dict):
                attachments_input = body.get("anexos") or body.get("attachments")
    except Exception:
        attachments_input = None

    # Extract status code from various input formats
    code_val = None
    
    if isinstance(new_status, (str, int)):
        s = str(new_status).strip()
        if s.startswith("{") or s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict) and "code" in parsed:
                    code_val = str(parsed["code"])
            except Exception:
                pass
        if code_val is None:
            code_val = s
    elif isinstance(new_status, dict):
        if "code" in new_status:
            code_val = str(new_status["code"])
    elif hasattr(new_status, "code"):
        code_val = str(new_status.code)

    if not code_val:
        raise HTTPException(400, "Invalid status: provide a code, e.g., {\"code\": \"1\"}")

    if code_val not in VALID_CODES_SET:
        raise HTTPException(400, "Invalid tracking code")

    # Update shipment status
    status_model = ShipmentStatus(code=code_val)
    shipment.status = status_model.model_dump()
    await db.commit()
    await db.refresh(shipment)

    # Process attachments
    attachment_service = AttachmentService()
    final_attachments = []

    # Single file from multipart
    if attachment:
        content = await attachment.read()
        saved = attachment_service.save_file(content, original_name=getattr(attachment, "filename", None))
        b64 = base64.b64encode(content).decode()
        final_attachments.append({"arquivo": {"nome": saved["url"], "dados": b64}})

    # Attachments from JSON body
    if attachments_input:
        for item in attachments_input:
            arquivo = item.get("arquivo", {})
            nome = arquivo.get("nome")
            dados = arquivo.get("dados")
            if dados:
                saved = attachment_service.save_base64(dados, original_name=None)
                final_attachments.append({"arquivo": {"nome": saved["url"], "dados": dados}})
            elif nome and nome.startswith("http"):
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(nome)
                    if r.status_code < 300:
                        content = r.content
                        saved = attachment_service.save_file(content, original_name=nome.split("/")[-1])
                        b64 = base64.b64encode(content).decode()
                        final_attachments.append({"arquivo": {"nome": saved["url"], "dados": b64}})
                except Exception:
                    continue

    # Send tracking events for each CTe
    results = []
    for cte in shipment.client_ctes:
        for nf in cte.invoices:
            success, resp_text = await tracking_service.send(
                document_key=nf,
                event_code=code_val,
                attachments=final_attachments,
            )
            results.append({
                "cte": str(cte.id),
                "nf": nf,
                "ok": success,
                "response": resp_text[:500] if resp_text else None,
            })

        # Register tracking event
        await TrackingEventService.register(
            db,
            TrackingEventCreate(
                client_cte_id=cte.id,
                event_code=code_val,
                description=VALID_CODES[code_val]["message"],
                event_date=datetime.datetime.now(datetime.timezone.utc),
            ),
        )

    return {
        "status": "ok",
        "code_sent": code_val,
        "results": results,
    }


# ---------------------------
# VBLOG Sync (Open Transits → CT-es)
# ---------------------------

@router.post("/sync")
async def sync_shipments_from_vblog(
    dry_run: bool = False,
    db: AsyncSession = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
):
    """
    Sync shipments from VBLOG open transits:
    - Queries open transits
    - Extracts CTe access keys
    - Downloads CTe XMLs
    - Persists new `Shipment` + `ClientCTe` or updates existing CT-es

    Query params:
    - dry_run: When true, performs no DB writes; returns summary only.
    """

    # Ensure VBLOG is configured
    if not (vblog.cnpj and vblog.token and vblog.base_url):
        raise HTTPException(400, "VBLOG configuration missing: cnpj/token/base_url")

    # Query open transits
    transit_resp = await vblog.query_open_transits()
    if not transit_resp.transits:
        return {
            "status": "ok",
            "found_keys": 0,
            "created": 0,
            "updated": 0,
            "details": [],
            "warnings": transit_resp.warnings,
            "code": transit_resp.code,
            "description": transit_resp.description,
        }

    # Collect CTe keys from transits
    keys: set[str] = set()
    for ct in transit_resp.transits:
        for doc in ct.docs:
            local_type = (doc.type or "").lower()
            if local_type == "chavecte" and doc.value:
                key = doc.value.strip()
                if len(key) >= 20:  # basic sanity
                    keys.add(key)
            elif local_type == "xml" and doc.value:
                try:
                    # Try to extract chCTe from inline XML
                    k = VBlogTransitoService.extract_xml_key(doc.value, key_tag="chCTe")
                    if k:
                        keys.add(k)
                except Exception:
                    continue

    if not keys:
        return {
            "status": "ok",
            "found_keys": 0,
            "created": 0,
            "updated": 0,
            "details": [],
            "warnings": transit_resp.warnings + ["No CTe keys found in transits"],
            "code": transit_resp.code,
            "description": transit_resp.description,
        }

    # Helper: extract NF-e keys from a CTe XML string
    def extract_nfe_keys(cte_xml: Optional[str]) -> list[str]:
        if not cte_xml:
            return []
        try:
            root = ET.fromstring(cte_xml)
        except Exception:
            return []
        found: list[str] = []
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "chNFe" and elem.text:
                val = elem.text.strip()
                if val:
                    found.append(val)
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for x in found:
            if x not in seen:
                unique.append(x)
                seen.add(x)
        return unique

    # Prepare CTe downloader
    cte_downloader = VBlogCTeService(vblog)

    created = 0
    updated = 0
    details = []
    errors = []

    for key in sorted(keys):
        try:
            existing = await ClientCTeService.get_by_access_key(db, key)

            # Download XML (best-effort)
            xml_cte = await cte_downloader.download_cte(key)
            nfe_keys = extract_nfe_keys(xml_cte)

            if dry_run:
                details.append({
                    "key": key,
                    "action": "skipped",
                    "has_xml": bool(xml_cte),
                    "nfe_count": len(nfe_keys),
                })
                continue

            if existing:
                # Update XML and invoices if available
                if xml_cte:
                    existing = await ClientCTeService.update_xml(db, existing, xml_cte)
                if nfe_keys:
                    existing = await ClientCTeService.update_invoices(db, existing, nfe_keys)
                updated += 1
                details.append({
                    "key": key,
                    "action": "updated",
                    "has_xml": bool(xml_cte),
                    "nfe_count": len(nfe_keys),
                })
            else:
                # Create a new shipment and attach the CTe
                shipment = await ShipmentService.create(db, ShipmentCreate())
                cte = await ClientCTeService.add(
                    db,
                    shipment_id=shipment.id,
                    data=ClientCTeCreate(access_key=key, xml=xml_cte),
                )
                if nfe_keys:
                    await ClientCTeService.update_invoices(db, cte, nfe_keys)
                created += 1
                details.append({
                    "key": key,
                    "action": "created",
                    "shipment_id": str(shipment.id),
                    "has_xml": bool(xml_cte),
                    "nfe_count": len(nfe_keys),
                })

        except Exception as e:
            msg = f"CTe {key} error: {e}"
            logger.error(msg)
            errors.append(msg)

    return {
        "status": "ok",
        "found_keys": len(keys),
        "created": created,
        "updated": updated,
        "details": details,
        "errors": errors,
        "warnings": transit_resp.warnings,
        "code": transit_resp.code,
        "description": transit_resp.description,
    }
