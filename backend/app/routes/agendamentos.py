from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import SessionLocal
from app.services.agendamento_service import AgendamentoService
from app.services.carga_service import CargaService
from app.schemas.agendamento import AgendamentoCreate, AgendamentoRead


router = APIRouter(
    prefix="/cargas",
    tags=["Agendamentos"]
)


# ---------------------
# Dependência do DB
# ---------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------
# GET — obter agendamento
# ---------------------
@router.get("/{carga_id}/agendamento", response_model=AgendamentoRead)
def obter_agendamento(
    carga_id: UUID,
    db: Session = Depends(get_db),
):
    ag = AgendamentoService.obter_por_carga(db, carga_id)
    if not ag:
        raise HTTPException(404, "Agendamento não encontrado")

    return ag


# ---------------------
# PUT — criar ou atualizar
# ---------------------
@router.put("/{carga_id}/agendamento", response_model=AgendamentoRead)
def atualizar_agendamento(
    carga_id: UUID,
    data: AgendamentoCreate,
    db: Session = Depends(get_db),
):

    # ⚠️ Garantir que o carga_id do body seja igual ao da rota
    if data.carga_id != carga_id:
        raise HTTPException(
            400,
            "O campo 'carga_id' do agendamento deve ser igual ao ID da rota."
        )

    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    ag = AgendamentoService.criar_ou_atualizar(db, data)
    return ag


# ---------------------
# DELETE — remover agendamento (opcional)
# ---------------------
@router.delete("/{carga_id}/agendamento")
def remover_agendamento(
    carga_id: UUID,
    db: Session = Depends(get_db),
):
    ag = AgendamentoService.obter_por_carga(db, carga_id)
    if not ag:
        raise HTTPException(404, "Agendamento não encontrado")

    db.delete(ag)
    db.commit()

    return {"status": "agendamento removido"}
