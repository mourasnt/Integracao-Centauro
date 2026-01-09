# app/schemas/carga.py
from pydantic import BaseModel
from typing import Optional, List
import uuid
from app.models.carga import CargaStatus
from .cte_cliente import CTeClienteRead
from .cte_subcontratacao import CTeSubRead
from .agendamento import AgendamentoRead


class UFInfo(BaseModel):
    cod: Optional[str] = None
    uf: Optional[str] = None

class MunicipioInfo(BaseModel):
    cod: Optional[str] = None
    municipio: Optional[str] = None

class CargaBase(BaseModel):
    id_3zx: Optional[str] = None
    id_cliente: Optional[str] = None

    origem_uf: Optional[UFInfo] = None
    origem_municipio: Optional[MunicipioInfo] = None

    destino_uf: Optional[UFInfo] = None
    destino_municipio: Optional[MunicipioInfo] = None


class CargaCreate(CargaBase):
    """Usado para criar cargas automaticamente ao consultar a API VBLOG."""
    pass


class CargaUpdate(CargaBase):
    """Atualização parcial."""
    status: Optional[CargaStatus] = None


class CargaStatusIn(BaseModel):
    """Input model used by endpoints to accept only the code for status updates."""
    code: str


class CargaRead(CargaBase):
    id: uuid.UUID
    status: CargaStatus

    ctes_cliente: List[CTeClienteRead] = []
    ctes_subcontratacao: List[CTeSubRead] = []
    agendamento: Optional[AgendamentoRead] = None

    class Config:
        from_attributes = True
