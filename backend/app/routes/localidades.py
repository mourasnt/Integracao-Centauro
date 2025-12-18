from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.schemas.localidade import EstadoRead, MunicipioRead
from app.services.localidades_service import LocalidadesService

router = APIRouter(prefix="/localidades", tags=["Localidades"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/estados", response_model=list[EstadoRead])
def listar_estados(db: Session = Depends(get_db)):
    return LocalidadesService.get_estados(db)


@router.get("/estados/{uf}/municipios", response_model=list[MunicipioRead])
def listar_municipios_uf(uf: str, db: Session = Depends(get_db)):
    municipios = LocalidadesService.get_municipios_por_uf(db, uf)
    if municipios is None:
        raise HTTPException(404, "UF não encontrada")
    return municipios


@router.get("/municipios/{codigo_ibge}", response_model=MunicipioRead)
def obter_municipio(codigo_ibge: int, db: Session = Depends(get_db)):
    muni = LocalidadesService.get_municipio_por_codigo(db, codigo_ibge)
    if not muni:
        raise HTTPException(404, "Município não encontrado")
    return muni


@router.post("/sincronizar")
def sincronizar(db: Session = Depends(get_db)):
    LocalidadesService.sincronizar_com_ibge(db)
    return {"status": "ok", "mensagem": "Localidades atualizadas com IBGE"}
