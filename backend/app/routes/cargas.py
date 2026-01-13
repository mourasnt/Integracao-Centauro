from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi import File, UploadFile

from fastapi import Form  # type: ignore

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
# authentication removed: endpoints are now public
from app.schemas.carga import CargaStatus
from fastapi import Body
from typing import Optional, List, Any
from pathlib import Path
from app.schemas.carga import CargaStatusIn
from app.services.constants import FINISH_CODES, VALID_CODES, VALID_CODES_SET
from app.services.vblog_tracking import VBlogTrackingService
import datetime
from fastapi.responses import StreamingResponse
from io import BytesIO
import os

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
    cnpj = os.getenv("VBLOG_CNPJ")
    token = os.getenv("VBLOG_TOKEN")
    return VBlogTransitoService(
        cnpj=cnpj,
        token=token,
    )


# ---------------------------
# ROTAS CRUD BÁSICO
# ---------------------------

@router.get("/", response_model=list[CargaRead])
def listar_cargas(
    db: Session = Depends(get_db),
):
    return CargaService.listar_cargas(db)


@router.get("/{carga_id}", response_model=CargaRead)
def obter_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
):
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")
    return carga


@router.post("/", response_model=CargaRead)
def criar_carga(
    data: CargaCreate,
    db: Session = Depends(get_db),
):
    return CargaService.criar_carga(db, data)


@router.put("/{carga_id}", response_model=CargaRead)
def atualizar_carga(
    carga_id: UUID,
    data: CargaUpdate,
    db: Session = Depends(get_db),
):
    carga = CargaService.atualizar_carga(db, carga_id, data)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")
    return carga


@router.delete("/{carga_id}")
def deletar_carga(
    carga_id: UUID,
    db: Session = Depends(get_db),
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
):

    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    integrator = TransitoIntegrationService(vblog)
    atualizados = await integrator.baixar_ctes_da_carga(db, carga)

    return atualizados


@router.post("/{carga_id}/adicionar-nfs", response_model=list[CTeClienteRead])
async def adicionar_nfs_a_ctes(
    carga_id: UUID,
    db: Session = Depends(get_db),
    vblog: VBlogTransitoService = Depends(get_vblog_service),
):
    """Extrai NFs dos XMLs dos CT-es dessa carga e persiste em cada CTe."""
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    integrator = TransitoIntegrationService(vblog)

    atualizados = []

    for cte in carga.ctes_cliente:
        # Só processa CT-es que já têm XML salvo
        if not cte.xml_encrypted:
            continue
        try:
            nfs = await integrator.extrair_nfs_cte(cte.xml)
            cte.nfs = nfs
            db.add(cte)
            atualizados.append(cte)
        except Exception as e:
            print(f"Aviso: falha ao extrair NFs para CT-e {cte.chave}: {e}")

    if atualizados:
        db.commit()

    return atualizados


# ---------------------------
# 3) Obter CT-e individual descriptografado
# ---------------------------

@router.get("/cte/{cte_id}", response_model=CTeClienteRead)
def obter_cte(
    cte_id: UUID,
    db: Session = Depends(get_db),
):
    cte = CTeClienteService.obter_por_id(db, cte_id)
    if not cte:
        raise HTTPException(404, "CT-e não encontrado")
    return cte

@router.get("/cte/{cte_id}/download")
def download_cte_xml(
    cte_id: UUID,
    db: Session = Depends(get_db),
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
    novo_status: Optional[Any] = Body(None, example={"code": "1"}),
    anexo: Optional[UploadFile] = File(None),
    request: Request = None,
    db: Session = Depends(get_db),
):
    # Note: OpenAPI shows `novo_status` (example with {"code":"1"}) and `anexo` (file). Internally we accept string or object for `novo_status` and also a hidden `anexos` JSON field.
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    # Support JSON body with an `anexos` field (not exposed in OpenAPI) and multipart form with `anexo` file.
    if request is not None and request.headers.get("content-type", "").startswith("multipart/"):
        try:
            form = await request.form()
            novo_status_json = form.get("novo_status_json") or form.get("novo_status")
            if novo_status_json:
                from app.schemas.carga import CargaStatusIn
                try:
                    novo_status = CargaStatusIn.model_validate_json(novo_status_json)
                except Exception as e:
                    raise HTTPException(400, f"Erro ao parsear novo_status via form: {e}")
        except Exception:
            # form parsing may fail if python-multipart is not installed; ignore and rely on body param
            pass

    anexos_input = None
    try:
        if request is not None and request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
            if isinstance(body, dict):
                anexos_input = body.get("anexos")
    except Exception:
        anexos_input = None

    import json

    # Accept `novo_status` in several forms and prefer a raw code string/number:
    # - raw code: "1" or 1
    # - simple JSON string: "{\"code\":\"1\"}"
    # - dict/object containing {'code': '1'}

    code_val = None

    # primitive (string/number) — treat as raw code unless it looks like a JSON object
    if isinstance(novo_status, (str, int)):
        s = str(novo_status).strip()
        if s.startswith("{") or s.startswith("["):
            # possible JSON; try to parse and extract code
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict) and "code" in parsed:
                    code_val = str(parsed["code"])
            except Exception:
                pass
        if code_val is None:
            # treat the primitive directly as code
            code_val = s
    elif isinstance(novo_status, dict):
        if "code" in novo_status:
            code_val = str(novo_status["code"])
    elif hasattr(novo_status, "code"):
        code_val = str(novo_status.code)

    if not code_val:
        raise HTTPException(400, "novo_status inválido: forneça apenas o código, ex: {\"novo_status\": \"1\"}")

    if code_val not in VALID_CODES_SET:
        raise HTTPException(400, "Código tracking inválido")

    code_to_send = code_val

    # Build full status model using domain model to auto-fill message/type
    from app.models.carga import CargaStatus as ModelCargaStatus
    novo_status_model = ModelCargaStatus(code=code_to_send)
    carga.status = novo_status_model.model_dump()

    if not code_to_send:
        # nada a enviar (ex.: PENDENTE ou status sem mapeamento)
        return {"status": "ok", "codigo_enviado": None}

    # Process attachments (single file `anexo` and JSON `anexos` if provided)
    from app.services.attachments_service import AttachmentService
    import base64
    import httpx

    attachment_svc = AttachmentService()

    anexos_final = []

    # single file from multipart/form-data (field 'anexo')
    if anexo:
        content = await anexo.read()
        saved = attachment_svc.save_file(content, original_name=getattr(anexo, "filename", None))
        b64 = base64.b64encode(content).decode()
        anexos_final.append({"arquivo": {"nome": saved["url"], "dados": b64}})

    # anexos from JSON body (not exposed in openapi schema)
    if anexos_input:
        for item in anexos_input:
            arquivo = item.get("arquivo", {})
            nome = arquivo.get("nome")
            dados = arquivo.get("dados")
            if dados:
                saved = attachment_svc.save_base64(dados, original_name=None)
                anexos_final.append({"arquivo": {"nome": saved["url"], "dados": dados}})
            elif nome and nome.startswith("http"):
                try:
                    async with httpx.AsyncClient() as client:
                        r = await client.get(nome)
                    if r.status_code < 300:
                        content = r.content
                        saved = attachment_svc.save_file(content, original_name=Path(nome).name)
                        b64 = base64.b64encode(content).decode()
                        anexos_final.append({"arquivo": {"nome": saved["url"], "dados": b64}})
                except Exception:
                    continue

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
            #if last_code in FINISH_CODES:
            #    results.append({"cte": str(cte.id), "ok": False, "reason": "CT-e já em estado final"})
            #    continue
        
        # registrar tracking interno
        from app.schemas.tracking import TrackingCreate
        from app.services.tracking_service import TrackingService
        for nf in cte.nfs:

            success, resp_text = await tv.enviar(nf, code_to_send, anexos=anexos_final)
            results.append({"cte": str(cte.id), "nf": nf, "ok": success, "vblog_response": resp_text[:500]})

        TrackingService.registrar(
                db,
                TrackingCreate(
                    cte_cliente_id=cte.id,
                    codigo_evento=code_to_send,
                    descricao=VALID_CODES[code_to_send]["message"],
                    data_evento=datetime.datetime.now(datetime.timezone.utc)
                )
            )

    return {"status": "ok", "codigo_enviado": code_to_send, "results": results}