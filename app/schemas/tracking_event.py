# app/schemas/tracking_event.py
"""
TrackingEvent schemas (formerly tracking.py).
Pydantic models for tracking event API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
import datetime
import uuid


class TrackingEventBase(BaseModel):
    """Base tracking event schema."""
    client_cte_id: uuid.UUID = Field(..., alias="cte_cliente_id")
    invoice_key: Optional[str] = Field(None, alias="chave_nf")
    event_code: str = Field(..., alias="codigo_evento")
    description: str = Field(..., alias="descricao")
    event_date: datetime.datetime = Field(..., alias="data_evento")

    class Config:
        populate_by_name = True


class TrackingEventCreate(TrackingEventBase):
    """Schema for creating a tracking event."""
    pass


class TrackingEventRead(TrackingEventBase):
    """Schema for reading a tracking event."""
    id: uuid.UUID

    class Config:
        from_attributes = True
        populate_by_name = True

