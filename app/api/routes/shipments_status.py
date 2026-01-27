# app/api/routes/shipments_status.py
"""
Status update operations with tracking for shipments.
"""

from uuid import UUID
from typing import Optional, Any
import json
import base64
import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.api.deps import get_db, get_tracking_service
from app.services.shipment_service import ShipmentService
from app.services.tracking_event_service import TrackingEventService
from app.services.attachments_service import AttachmentService
from app.services.vblog.tracking import VBlogTrackingService
from app.services.constants import VALID_CODES, VALID_CODES_SET
from app.schemas.tracking_event import TrackingEventCreate
from app.models.shipment import ShipmentStatus


router = APIRouter()


def parse_status_code(new_status: Any) -> Optional[str]:
    """
    Extract status code from various input formats.
    
    Accepts:
    - Raw code: "1" or 1
    - JSON string: '{"code": "1"}'
    - Object: {"code": "1"}
    - Object with .code attribute
    
    Returns the extracted code string or None.
    """
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
    
    return code_val


async def parse_form_status(request: Request) -> Optional[Any]:
    """Parse status from multipart form data."""
    try:
        form = await request.form()
        status_json = form.get("novo_status_json") or form.get("novo_status") or form.get("new_status")
        if status_json:
            from app.schemas.shipment import ShipmentStatusInput
            return ShipmentStatusInput.model_validate_json(status_json)
    except Exception:
        pass
    return None


async def parse_json_attachments(request: Request) -> Optional[list]:
    """Parse attachments from JSON body."""
    try:
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
            if isinstance(body, dict):
                return body.get("anexos") or body.get("attachments")
    except Exception:
        pass
    return None


async def process_attachments(
    attachment: Optional[UploadFile],
    attachments_input: Optional[list],
    attachment_service: AttachmentService,
) -> list[dict]:
    """Process and save attachments from various sources."""
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

    return final_attachments


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
        form_status = await parse_form_status(request)
        if form_status:
            new_status = form_status

    # Parse attachments from JSON body
    attachments_input = await parse_json_attachments(request) if request else None

    # Extract status code
    code_val = parse_status_code(new_status)

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
    final_attachments = await process_attachments(attachment, attachments_input, attachment_service)

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
