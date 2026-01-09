# app/routes/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from uuid import UUID
import datetime

from app.core.database import SessionLocal
from app.services.vblog_tracking import VBlogTrackingService
from app.services.tracking_service import TrackingService
from app.services.cte_cliente_service import CTeClienteService
from app.services.constants import VALID_CODES

from app.schemas.tracking import TrackingCreate

router = APIRouter(tags=["Tracking"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/tracking/{cte_id}/reenviar")
async def reenviar_tracking(
    cte_id: UUID,
    codigo_evento: str = Body(...),
    db: Session = Depends(get_db),
):
    if codigo_evento not in VALID_CODES:
        raise HTTPException(400, "Código VBLOG inválido")

    cte = CTeClienteService.obter_por_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CT-e não encontrado")

    tv = VBlogTrackingService()
    success, resp_text = await tv.enviar(cte.chave, codigo_evento)

    # registrar tentativa
    TrackingService.registrar(
        db,
        TrackingCreate(
            cte_cliente_id=cte.id,
            codigo_evento=codigo_evento,
            descricao=VALID_CODES[codigo_evento]["message"],
            data_evento=datetime.now(datetime.timezone.utc)
        )
    )
    return {"ok": success, "vblog_response": resp_text}
