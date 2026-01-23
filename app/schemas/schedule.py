# app/schemas/schedule.py
"""
Schedule schemas (formerly agendamento.py).
Pydantic models for schedule API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
import datetime
import uuid


class ScheduleBase(BaseModel):
    """Base schedule schema."""
    # ETA (Arrival at destination)
    eta_scheduled: Optional[datetime.datetime] = Field(None, alias="eta_programado")
    eta_actual: Optional[datetime.datetime] = Field(None, alias="eta_realizado")
    eta_departure: Optional[datetime.datetime] = Field(None, alias="eta_saida")

    # ETD (Departure from origin)
    etd_scheduled: Optional[datetime.datetime] = Field(None, alias="etd_programado")
    etd_actual: Optional[datetime.datetime] = Field(None, alias="etd_realizado")
    etd_completed: Optional[datetime.datetime] = Field(None, alias="etd_finalizado")

    class Config:
        populate_by_name = True


class ScheduleCreate(ScheduleBase):
    """Schema for creating a schedule."""
    shipment_id: uuid.UUID = Field(..., alias="carga_id")

    class Config:
        populate_by_name = True


class ScheduleRead(ScheduleBase):
    """Schema for reading a schedule."""
    id: uuid.UUID
    shipment_id: uuid.UUID = Field(..., alias="carga_id")

    class Config:
        from_attributes = True
        populate_by_name = True

