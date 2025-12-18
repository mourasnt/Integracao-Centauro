# app/schemas/agendamento.py
from pydantic import BaseModel
from typing import Optional
import datetime
import uuid


class AgendamentoBase(BaseModel):
    eta_programado: Optional[datetime.datetime] = None
    eta_realizado: Optional[datetime.datetime] = None
    eta_saida: Optional[datetime.datetime] = None

    etd_programado: Optional[datetime.datetime] = None
    etd_realizado: Optional[datetime.datetime] = None
    etd_finalizado: Optional[datetime.datetime] = None


class AgendamentoCreate(AgendamentoBase):
    carga_id: uuid.UUID


class AgendamentoRead(AgendamentoBase):
    id: uuid.UUID
    carga_id: uuid.UUID

    class Config:
        from_attributes = True
