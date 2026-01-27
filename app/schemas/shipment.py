# app/schemas/shipment.py
"""
Shipment schemas (formerly carga.py).
Pydantic models for shipment API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
import uuid

from app.models.shipment import ShipmentStatus


class StateInfo(BaseModel):
    """State reference information."""
    code: Optional[str] = Field(None, alias="cod")
    abbreviation: Optional[str] = Field(None, alias="uf")

    class Config:
        populate_by_name = True


class CityInfo(BaseModel):
    """City reference information."""
    code: Optional[str] = Field(None, alias="cod")
    name: Optional[str] = Field(None, alias="municipio")

    class Config:
        populate_by_name = True


class ShipmentBase(BaseModel):
    """Base shipment schema."""
    external_id: Optional[str] = Field(None, alias="id_3zx")
    client_id: Optional[str] = Field(None, alias="id_cliente")

    origin_state: Optional[StateInfo] = Field(None, alias="origem_uf")
    origin_city: Optional[CityInfo] = Field(None, alias="origem_municipio")
    destination_state: Optional[StateInfo] = Field(None, alias="destino_uf")
    destination_city: Optional[CityInfo] = Field(None, alias="destino_municipio")

    class Config:
        populate_by_name = True


class ShipmentCreate(ShipmentBase):
    """Schema for creating a shipment."""
    pass


class ShipmentUpdate(ShipmentBase):
    """Schema for updating a shipment."""
    status: Optional[ShipmentStatus] = None


class ShipmentStatusInput(BaseModel):
    """Input schema for status updates (code only)."""
    code: str


class ShipmentRead(ShipmentBase):
    """Schema for reading a shipment with relationships."""
    id: uuid.UUID
    status: ShipmentStatus

    # Relationships - imported here to avoid circular imports
    client_ctes: List[Any] = Field(default_factory=list, alias="ctes_cliente")
    subcontracted_ctes: List[Any] = Field(default_factory=list, alias="ctes_subcontratacao")

    class Config:
        from_attributes = True
        populate_by_name = True

