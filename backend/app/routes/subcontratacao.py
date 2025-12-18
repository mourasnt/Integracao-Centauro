from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from uuid import UUID
import xml.etree.ElementTree as ET

from app.core.database import SessionLocal
from app.models.user import User
from app.services.carga_service import CargaService
from app.services.crypto_service import encrypt_text
from app.models.cte_subcontratacao import CTeSubcontratacao
from app.schemas.cte_subcontratacao import CTeSubRead
from app.routes.users import get_current_user

router = APIRouter(prefix="/subcontratacao", tags=["Subcontratação"])


# ---------------------
# Dependências
# ---------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------
# Função auxiliar — extrair chave do XML
# ---------------------
def extrair_chave_do_xml(xml_str: str) -> str | None:
    try:
        root = ET.fromstring(xml_str)
        ns = {"cte": "http://www.portalfiscal.inf.br/cte"}

        ch = root.find(".//cte:chCTe", ns)
        if ch is not None and ch.text:
            return ch.text.strip()
    except Exception as e:
        print("Erro ao extrair chave:", e)
    return None


# ---------------------
# Upload XML Subcontratação
# ---------------------
@router.post(
    "/upload-xml",
    response_model=CTeSubRead,
    summary="Faz upload do XML de subcontratação e vincula a uma carga."
)
async def upload_xml_subcontratacao(
    carga_id: UUID,
    arquivo: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Validar carga
    carga = CargaService.obter_por_id(db, carga_id)
    if not carga:
        raise HTTPException(404, "Carga não encontrada")

    # 2. Ler XML enviado
    xml_str = (await arquivo.read()).decode("utf-8")

    # 3. Extrair chave automaticamente
    chave = extrair_chave_do_xml(xml_str)

    if not chave:
        raise HTTPException(400, "Não foi possível extrair a chave do XML enviado.")

    # 4. Criar registro de subcontratação
    sub = CTeSubcontratacao(
        carga_id=carga_id,
        chave=chave,
        xml_encrypted=encrypt_text(xml_str),
    )

    db.add(sub)
    db.commit()
    db.refresh(sub)

    return sub


# ---------------------
# Consultar subcontratação
# ---------------------
@router.get("/{sub_id}", response_model=CTeSubRead)
def obter_subcontratacao(
    sub_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    sub = db.query(CTeSubcontratacao).filter(CTeSubcontratacao.id == sub_id).first()
    if not sub:
        raise HTTPException(404, "Subcontratação não encontrada")
    return sub
