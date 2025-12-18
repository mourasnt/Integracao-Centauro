# app/schemas/cte_subcontratacao.py
from pydantic import BaseModel
from typing import Optional
import uuid


class CTeSubBase(BaseModel):
    chave: str


class CTeSubCreate(CTeSubBase):
    xml: Optional[str] = None


class CTeSubRead(CTeSubBase):
    id: uuid.UUID
    carga_id: uuid.UUID
    xml: Optional[str] = None

    class Config:
        from_attributes = True
