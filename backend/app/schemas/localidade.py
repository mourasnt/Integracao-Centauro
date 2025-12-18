from pydantic import BaseModel
import uuid
from typing import List


class EstadoBase(BaseModel):
    nome: str
    sigla: str
    codigo_ibge: int


class EstadoRead(EstadoBase):
    id: uuid.UUID

    class Config:
        from_attributes = True


class MunicipioBase(BaseModel):
    nome: str
    codigo_ibge: int
    estado_id: uuid.UUID


class MunicipioRead(MunicipioBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
