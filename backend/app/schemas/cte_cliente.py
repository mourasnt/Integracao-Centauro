# app/schemas/cte_cliente.py
from pydantic import BaseModel
from typing import Optional
import uuid


class CTeClienteBase(BaseModel):
    chave: str


class CTeClienteCreate(CTeClienteBase):
    xml: Optional[str] = None  # XML descriptografado


class CTeClienteRead(CTeClienteBase):
    id: uuid.UUID
    carga_id: uuid.UUID
    xml: Optional[str] = None  # já descriptografado

    class Config:
        from_attributes = True
