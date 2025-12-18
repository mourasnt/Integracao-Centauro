from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.carga import CargaCreate, CargaUpdate, CargaRead
from app.schemas.cte_cliente import CTeClienteRead
from app.services.carga_service import CargaService
from app.services.cte_cliente_service import CTeClienteService
from app.services.vblog_transito import VBlogTransitoService
from app.services.transito_integration_service import TransitoIntegrationService
from app.routes.users import get_current_user, require_admin
from app.schemas.carga import CargaStatus
from fastapi import Body
from typing import Optional
from app.services.constants import FINISH_CODES, VALID_CODES, VALID_CODES_SET
from app.services.vblog_tracking import VBlogTrackingService
import datetime
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter(prefix="/cargas", tags=["Cargas"])


# ---------------------------
# Dependências
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_vblog_service() -> VBlogTransitoService:
    # Em produção puxar de variáveis de ambiente!
    return VBlogTransitoService(
        cnpj="34790798000134",
        token="t2SNUKi7pt6D9pbEoJVC"
    )


# ---------------------------
# ROTAS CRUD BÁSICO
# ---------------------------

@router.get("/", response_model=list[CargaRead])
def listar_cargas(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return CargaService.listar_cargas(db)


@router.get("/{carga_id}", response_model=CargaRead)
def obter_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")
    return carga


@router.post("/", response_model=CargaRead)
def criar_carga(
    data: CargaCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return CargaService.criar_carga(db, data)


@router.put("/{carga_id}", response_model=CargaRead)
def atualizar_carga(
    carga_id: UUID,
    data: CargaUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    carga = CargaService.atualizar_carga(db, carga_id, data)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")
    return carga


@router.delete("/{carga_id}")
def deletar_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ok = CargaService.deletar_carga(db, carga_id)
    if not ok:
        raise HTTPException(404, "Carga não encontrada")
    return {"status": "deleted"}


# ---------------------------
# 1) Sincronizar trânsitos VBLOG
# ---------------------------

@router.post("/sync-vblog", response_model=list[CargaRead])
async def sincronizar_transitos(
    db: Session = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
    _: User = Depends(require_admin),
):
    integrator = TransitoIntegrationService(vblog)
    cargas = await integrator.sincronizar_transitos_abertos(db)
    return cargas


# ---------------------------
# 2) Baixar XML completo dos CT-es da carga
# ---------------------------

@router.post("/{carga_id}/baixar-ctes", response_model=list[CTeClienteRead])
async def baixar_ctes(
    carga_id: UUID,
    db: Session = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
    _: User = Depends(get_current_user),
):

    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    integrator = TransitoIntegrationService(vblog)
    atualizados = await integrator.baixar_ctes_da_carga(db, carga)

    return atualizados


# ---------------------------
# 3) Obter CT-e individual descriptografado
# ---------------------------

@router.get("/cte/{cte_id}", response_model=CTeClienteRead)
def obter_cte(
    cte_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cte = CTeClienteService.obter_por_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CT-e não encontrado")
    return cte

@router.get("/cte/{cte_id}/download")
def download_cte_xml(
    cte_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cte = CTeClienteService.obter_por_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CT-e não encontrado")

    if not cte.xml:
        raise HTTPException(400, "CT-e não possui XML armazenado")

    # transforma texto em bytes
    xml_bytes = cte.xml.encode("utf-8")

    # cria um arquivo em memória
    file_stream = BytesIO(xml_bytes)

    # nome do arquivo
    filename = f"cte-{cte.id}.xml"

    return StreamingResponse(
        file_stream,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/{carga_id}/status")
async def alterar_status(
    carga_id: UUID,
    novo_status: CargaStatus = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")
    carga.status = novo_status.model_dump()

    # Decide código VBLOG a ser enviado
    code_to_send = None

    # 1) se foi enviado um código explicitamente, valide-o
    if carga.status["code"]:
        if str(carga.status["code"]) not in VALID_CODES_SET:
            raise HTTPException(400, "Código tracking inválido")
    else:
        raise HTTPException(400, "Código tracking não enviado")
    code_to_send = str(carga.status["code"])

    if not code_to_send:
        # nada a enviar (ex.: PENDENTE ou status sem mapeamento)
        return {"status": "ok", "codigo_enviado": None}

    # Atualiza status interno
    db.commit()
    db.refresh(carga)

    # Envia tracking para cada CT-e da carga
    tv = VBlogTrackingService()  # usa env vars se não passar cnpj/token
    results = []
    for cte in carga.ctes_cliente:
        # valida ordem de eventos: se já existir um evento final, bloqueia
        last_trackings = cte.trackings if hasattr(cte, "trackings") else []
        if last_trackings:
            last_code = last_trackings[-1].codigo_evento
            if last_code in FINISH_CODES:
                results.append({"cte": str(cte.id), "ok": False, "reason": "CT-e já em estado final"})
                continue

        success, resp_text = await tv.enviar(cte.chave, code_to_send)
        # registrar tracking interno
        from app.schemas.tracking import TrackingCreate
        from app.services.tracking_service import TrackingService

        TrackingService.registrar(
            db,
            TrackingCreate(
                cte_cliente_id=cte.id,
                codigo_evento=code_to_send,
                descricao=VALID_CODES[code_to_send]["message"],
                data_evento=datetime.datetime.now(datetime.timezone.utc)
            )
        )

        results.append({"cte": str(cte.id), "ok": success, "vblog_response": resp_text[:500]})

    return {"status": "ok", "codigo_enviado": code_to_send, "results": results}