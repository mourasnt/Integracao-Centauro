# app/api/routes/shipments_sync.py
"""
VBLOG synchronization operations for shipments.
"""

from typing import Optional
import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_vblog_service
from app.services.shipment_service import ShipmentService
from app.services.client_cte_service import ClientCTeService
from app.services.vblog.transito import VBlogTransitoService
from app.services.vblog.cte import VBlogCTeService
from app.schemas.shipment import ShipmentCreate
from app.schemas.client_cte import ClientCTeCreate
from app.utils.logger import logger


router = APIRouter()


def extract_nfe_keys(cte_xml: Optional[str]) -> list[str]:
    """Extract NF-e keys from a CTe XML string."""
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
            "raw_xml": transit_resp.raw_xml,
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
            "raw_xml": transit_resp.raw_xml,
        }

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
        "raw_xml": transit_resp.raw_xml,
    }
